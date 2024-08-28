import configparser
import os
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

DHT_CONFIG_NAME = "dht"

# Creation of the config parser
config = configparser.ConfigParser()
# The .ini file is located in the same folder of the config.py file, i.e. the config folder.
dir_path = os.path.dirname(os.path.realpath(__file__))
config_path = os.path.join(dir_path, "config.ini")
# We read the config file.
config.read(config_path)


def get_dht_parameters():
    """
    This method is used to get the DHT parameters
    :return: a config object that contains the value of the DHT parameters.
    """

    return config[DHT_CONFIG_NAME]

def get_private_key():
    """
    This method is used to get the private key
    :return:
    """
    # Get the host_key path
    host_key_path = config.get('DEFAULT', 'hostkey')

    # Read the host_key
    with open(host_key_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )
    if private_key is None:
        raise Exception("Unable to find or read file containing private key.")
    return private_key







