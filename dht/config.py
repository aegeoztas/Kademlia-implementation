import configparser
import os
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from typing import Tuple, Optional

DHT_CONFIG_NAME = "dht"

# Creation of the config parser
config = configparser.ConfigParser()
# The .ini file is the config folder.
parent_dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
config_path = os.path.join(parent_dir_path, "configuration", "config.ini")
# We read the config file.
config.read(config_path)


def get_dht_parameters():
    """
    This method is used to get the DHT parameters
    :return: a config object that contains the value of the DHT parameters.
    """

    return config[DHT_CONFIG_NAME]

def get_address_from_conf(address_name: str)->Tuple[Optional[str], Optional[int]]:
    try:
        api_ip, api_port = get_dht_parameters().get(address_name).split(':')
    except Exception:
        return None, None
    return api_ip, int(api_port)


def get_public_key():
    """
    This method is used to get the private key
    :return:
    """
    # Get the host_key path
    host_key_path = config.get('DEFAULT', 'hostkey')

    # Read the host_key
    with open(host_key_path, "rb") as key_file:
        public_key = serialization.load_pem_public_key(
            key_file.read(),
            backend=default_backend()
        )
    if public_key is None:
        raise Exception("Unable to find or read file containing public key.")
    return public_key







