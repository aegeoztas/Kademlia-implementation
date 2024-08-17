from enum import IntEnum
import os
from dotenv import load_dotenv

load_dotenv()
class Message(IntEnum):
    # Messages
    # DHT
    DHT_PUT = os.getenv("DHT_PUT")
    DHT_GET = os.getenv("DHT_GET")
    DHT_SUCCESS = os.getenv("DHT_SUCCESS")
    DHT_FAILURE = os.getenv("DHT_FAILURE")

    # KADEMLIA
    PING = os.getenv("PING")
    KADEMLIA_GET = os.getenv("KADEMLIA_GET")
    STORE = os.getenv("STORE")
    FIND_NODE = os.getenv("FIND_NODE")
    FIND_NODE_RESP = os.getenv("FIND_NODE_RESP")