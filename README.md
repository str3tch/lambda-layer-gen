# lambda-layer-gen
AWS Lambda which take a list of python packages, installs them and creates a Layer which other lambda's can use as dependencies 

## Pre Reqs

This uses the Serverless Framework to deploy. Install this via npm

 * `npm install -g serverless`

 ## Deploying

 Ensuring your AWS creds are setup, From this dir, just do:
  * `sls deploy`

## Testing

This is rough and ready.. no unit tests or nowt

to test, go to lambda console, and configure a test event with contents of _misc/test_event.json_

much quicker to use the lambda console in this instance as there's just a lot of fiddling to get this working

# Status so far

Lambda does not have `pip` installed, so I took a look at get_pip.py (copy in the _misc_ folder), and extracted pip.zip and imported that. Using the same _pip install_ functions as in get_pip.py, I use those to install the packages.

I can install *boto3, setuptools* and *wheel* just fine (last two are needed to install packages, as I have found out)


BUT.. *pyproj* fails to install. The difference is it's a tar.gz download (not a wheel), and these are installed by running `python setup.py egg.info` from within the inflated package zip folder. It fails because it can't find setuptools: 

```
ImportError: No module named setuptools
```

even though we have previously installed and put on the PYTHONPATH. I think the issue is that pip spawns a new process, which perhaps does not have the path setup correctly. If we can get setuptools to be recognised, we are away!

## Food for thought.

only /tmp is writable in lambda. This is what is causing the headache. I had to do some tricks to get things to work as much as they are :)

I've tried many ways to get `setuptools` to be recognised when installing `pyproj`, but to no avail!

Please go ahead and try.. but also, maybe this is not the right approach at all, and we need to scrap this idea and start again afresh

