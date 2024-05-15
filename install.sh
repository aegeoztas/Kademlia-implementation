# This script is used to initialize the python virtual environment on a linux machine.

# Note: use the command "source ./install.sh" to run this script.

# Creation of the virtual environment
python3 -m venv venv

# Activation of the virtual environment
source venv/bin/activate

# Update of pip
venv/bin/pip install --upgrade pip

# Installation of the packages required
venv/bin/pip install -r requirements.txt

# To activate the virtual environment once installed,  run "source ./venv/bin/activate"