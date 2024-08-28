import configparser
import os

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

def

# Get the host_key path
hostkey_path = config.get('DEFAULT', 'hostkey')

# Afficher le chemin de la clé
print("Hostkey path:", hostkey_path)

# Charger la clé privée depuis le chemin spécifié
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

with open(hostkey_path, "rb") as key_file:
    private_key = serialization.load_pem_private_key(
        key_file.read(),
        password=None,  # Remplacez par votre mot de passe si le fichier est chiffré
        backend=default_backend()
    )




