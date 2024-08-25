from enum import IntEnum
import os
from dotenv import load_dotenv

load_dotenv()
class Message(IntEnum):
    # Messages
    # DHT
    DHT_PUT = int(os.getenv("DHT_PUT"))
    DHT_GET = int(os.getenv("DHT_GET"))
    DHT_SUCCESS = int(os.getenv("DHT_SUCCESS"))
    DHT_FAILURE = int(os.getenv("DHT_FAILURE"))

    # KADEMLIA
    PING = int(os.getenv("PING"))
    FIND_VALUE = int(os.getenv("FIND_VALUE"))
    STORE = int(os.getenv("STORE"))
    FIND_NODE = int(os.getenv("FIND_NODE"))
    FIND_NODE_RESP = int(os.getenv("FIND_NODE_RESP"))
    FIND_VALUE_RESP = int(os.getenv("FIND_VALUE_RESP"))
    FIND_VALUE_FAILURE = int(os.getenv("FIND_VALUE_FAILURE"))

    PING_RESPONSE = int(os.getenv("PING_RESPONSE"))


# Fields sizes in number of bytes
SIZE_FIELD_SIZE = int(os.getenv("SIZE_FIELD_SIZE"))
MESSAGE_TYPE_FIELD_SIZE = int(os.getenv("MESSAGE_TYPE_FIELD_SIZE"))
KEY_SIZE = int(os.getenv("KEY_SIZE"))
IP_FIELD_SIZE = int(os.getenv("IP_FIELD_SIZE"))
PORT_FIELD_SIZE = int(os.getenv("PORT_FIELD_SIZE"))
RPC_ID_FIELD_SIZE = int(os.getenv("RPC_ID_FIELD_SIZE"))
NUMBER_OF_NODES_FIELD_SIZE = int(os.getenv("NUMBER_OF_NODES_FIELD_SIZE"))
TTL_FIELD_SIZE = int(os.getenv("TTL_FIELD_SIZE"))

# Global variables
NB_OF_CLOSEST_PEERS = int(os.getenv("NB_OF_CLOSEST_PEERS"))
MAX_TTL = int(os.getenv("MAX_TTL"))
K = int(os.getenv("K"))
