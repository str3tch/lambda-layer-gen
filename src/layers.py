import subprocess
import sys
import os
import zipfile
import json

# Lambda does not have pip, so use the packaged pip (in a zip) 
sys.path.append(os.getcwd() + '/src/pip.zip') 
import pip._internal

# The plan:
# Params in POST body:
#   - layer_name
#   - packages
#   - compatible_runtimes: list of runtimes: 'nodejs'|'nodejs4.3'|'nodejs6.10'|'nodejs8.10'|'java8'|'python2.7'|'python3.6'|'python3.7'|'dotnetcore1.0'|'dotnetcore2.0'|'dotnetcore2.1'|'nodejs4.3-edge'|'go1.x'|'ruby2.5'|'provided'
# * install boto3
# * add boto3 to path and import
# * import user's packages
# * zip them up
# * add to layer
# * return ARN of layer



def lambda_handler(event, context):
    print("event = {}".format(event))
    print("body = {}".format(event['body']))
    body = event['body']

    helper_dir = '/tmp/install'  # for the packages needed for installs, but not for adding to layer
    pkg_dir = '/tmp/python' # This dir will be zipped up to create the layer
    
    if os.path.isdir(pkg_dir) == False:
        os.mkdir(pkg_dir)
        os.mkdir(helper_dir)


    # Boto3 currently in lambda is out of date and does not support layers
    # So, install Boto3 to tmp dir, and then use that - so we can use publish_layer_version
    install(['boto3'], helper_dir)
    
    # these are needed to install packages
    install(['setuptools', 'wheel'], helper_dir)
    
    sys.path.insert(0, helper_dir) # Put new boto3 to front of path so we use this latest one
    os.environ['PYTHONPATH'] = helper_dir + ";" + os.environ['PYTHONPATH']
    print("PYTHONPATH: {}".format(os.environ['PYTHONPATH']))
    import boto3
    print("Boto3 version: {}".format(boto3.__version__))

    try:
        layer_name = body["layer_name"]
        type_name = body["compatible_runtime"]
    except KeyError as ke:
        print ("KeyError in getting params: {}".format(ke))
        return response("Mandatory params missing - need type (ie equipment, camera), type_name", 400)


    # FIXME get this one package installing.. currenlty does not 
    install(['pyproj'], pkg_dir)

    # FIXME use code below to install all desired packages.
    # packlist = body["packages"]
    # install(packlist, pkg_dir)


    try:
        # now zip up all packages
        zipfilename = '/tmp/layer.zip'
        make_zipfile(zipfilename, pkg_dir)
    
        # create a byte array
        with open(zipfilename, 'rb') as zip:
            f = zip.read()
            zip_bytearray = bytearray(f)

        # Now create / update layer
        lamb = boto3.client('lambda')
        results = lamb.publish_layer_version(LayerName=layer_name, CompatibleRuntimes=type_name, Content={ 'ZipFile' : zip_bytearray })
    except Exception as e:
        print ("Error creating layer: {}".format(e))
        # DEBUG ONLY, raise 
        raise e
        return response("Could not create layer", 400)

    return response(results, 200)

def install(packages, directory=''):
    print("Installing: {} into {}".format(packages, directory))

    try:
        if os.environ.get('PIP_REQ_TRACKER'):
            os.environ.pop('PIP_REQ_TRACKER')  # have to reset this because pip will try and use a non existant file otherwise, and will fail
            
        # Add -v for extra pip debug if needed
        args = ['install', "--upgrade",  "--force-reinstall", "--no-cache-dir", "-t", directory]
        args.extend(packages)
            
        pip._internal.main(args) 
    except Exception as e:
        print "Pip install failed:\n{}".format(e)



# Zip up a directory
def make_zipfile(output_filename, source_dir):
    relroot = os.path.abspath(os.path.join(source_dir, os.pardir))
    with zipfile.ZipFile(output_filename, "w", zipfile.ZIP_DEFLATED) as zip:
        for root, dirs, files in os.walk(source_dir):
            # add directory (needed for empty dirs)
            zip.write(root, os.path.relpath(root, relroot))
            for file in files:
                filename = os.path.join(root, file)
                if os.path.isfile(filename): # regular files only
                    arcname = os.path.join(os.path.relpath(root, relroot), file)
                    zip.write(filename, arcname)



    


######### AWS Gateway Response Related stuff #########

def response(payload, statusCode):
    return { 'statusCode': statusCode, 'body': json.dumps(payload) }

    

