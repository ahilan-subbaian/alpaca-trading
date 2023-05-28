#!/bin/bash

# define the directory and zip name
DIR="python"
ZIP_NAME="packages.zip"

# create a new virtual environment
python3 -m venv venv

# activate the virtual environment
source venv/bin/activate

for PACKAGE in "$@"
do
  # install the package without its dependencies
  pip install $PACKAGE -t $DIR
done

# deactivate the virtual environment
deactivate

# zip the packages
zip -r -9 $ZIP_NAME $DIR

# create a new layer and upload the zip file
aws lambda publish-layer-version --layer-name packages --zip-file fileb://$ZIP_NAME --compatible-runtimes python3.10

# clean up: remove the venv directory, the package directory and the zip file
rm -rf venv
rm -rf $DIR
rm $ZIP_NAME
