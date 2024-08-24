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
    FIND_VALUE_SUCCESS = int(os.getenv("FIND_VALUE_SUCCESS"))
    FIND_VALUE_FAILURE = int(os.getenv("FIND_VALUE_FAILURE"))

    PING_RESPONSE = int(os.getenv("PING_RESPONSE"))