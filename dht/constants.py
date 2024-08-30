from enum import IntEnum
import os
from dotenv import load_dotenv
import math
import config

# Load the global variables. They are all located in the .env file.
load_dotenv()

class Message(IntEnum):
    """
    This Enum contains the message number of every type of message that are used in this project.
    """

    # DHT API Message numbers
    DHT_PUT = int(os.getenv('DHT_PUT'))
    DHT_GET = int(os.getenv('DHT_GET'))
    DHT_SUCCESS = int(os.getenv('DHT_SUCCESS'))
    DHT_FAILURE = int(os.getenv('DHT_FAILURE'))

    # KADEMLIA peer-to-peer protocol message numbers
    PING = int(os.getenv('PING'))
    PING_RESPONSE = int(os.getenv('PING_RESPONSE'))

    STORE = int(os.getenv('STORE'))

    FIND_NODE = int(os.getenv('FIND_NODE'))
    FIND_NODE_RESP = int(os.getenv('FIND_NODE_RESP'))

    FIND_VALUE = int(os.getenv('FIND_VALUE'))
    FIND_VALUE_RESP = int(os.getenv('FIND_VALUE_RESP'))

    JOIN_NETWORK = int(os.getenv('JOIN_NETWORK'))
    JOIN_NETWORK_RESP = int(os.getenv('JOIN_NETWORK_RESP'))
    # reserved until 679 for DHT


# Message fields sizes in number of bytes
SIZE_FIELD_SIZE = int(os.getenv("SIZE_FIELD_SIZE"))
MESSAGE_TYPE_FIELD_SIZE = int(os.getenv("MESSAGE_TYPE_FIELD_SIZE"))
IP_FIELD_SIZE = int(os.getenv("IP_FIELD_SIZE"))
PORT_FIELD_SIZE = int(os.getenv("PORT_FIELD_SIZE"))
RPC_ID_FIELD_SIZE = int(os.getenv("RPC_ID_FIELD_SIZE"))
NUMBER_OF_NODES_FIELD_SIZE = int(os.getenv("NUMBER_OF_NODES_FIELD_SIZE"))
TTL_FIELD_SIZE = int(os.getenv("TTL_FIELD_SIZE"))
REPLICATION_FIELD_SIZE = int(os.getenv("REPLICATION_FIELD_SIZE"))
RESERVED_FIELD_SIZE = int(os.getenv("RESERVED_FIELD_SIZE"))


# Global variables
KEY_SIZE = int(os.getenv("KEY_SIZE")) # The size here is given in bytes.
KEY_BIT_LENGTH = KEY_SIZE * 8  # The size here is given in bits.
MAX_KEY_VALUE = int(math.pow(2, KEY_BIT_LENGTH)) - 1  # The maximum value a key of an object or node id can have
MAX_PORT_NUMBER = int(os.getenv("MAX_PORT_NUMBER"))



# DHT Parameters
parameters = config.get_dht_parameters()
ALPHA = int(parameters.get("ALPHA"))
K = int(parameters.get("K"))
MIN_TTL = int(parameters.get("MIN_TTL"))
MAX_TTL = int(parameters.get("MAX_TTL"))
TIME_OUT = int(parameters.get("TIME_OUT"))# The time-out in second used when sending requests.





