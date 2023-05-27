#!/bin/bash

# define the package name, directory and zip name
PACKAGE="alpaca-py"
DIR="python"
ZIP_NAME="$PACKAGE.zip"

# create a new virtual environment
python3 -m venv venv

# activate the virtual environment
source venv/bin/activate

# install the package without its dependencies
pip install $PACKAGE -t $DIR

# deactivate the virtual environment
deactivate

# zip the package
zip -r -9 $ZIP_NAME $DIR

# create a new layer and upload the zip file
# aws lambda publish-layer-version --layer-name $PACKAGE --zip-file fileb://$ZIP_NAME --compatible-runtimes python3.10

# clean up: remove the venv directory and the package directory
rm -rf venv
rm -rf $DIR
