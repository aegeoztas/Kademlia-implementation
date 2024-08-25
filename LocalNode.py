import hashlib
import asyncio
from LocalHashTable import *
from routing_table import *



class LocalNode:
    """
    This class represents the node linked to the instance of this program.
     It essentially contains the node's routing table and the node's storage.
    """

    def __init__(self, ip : str, port: int, host_key: str):
        self.ip: str = ip
        self.port: int = port


        # Creation of the node ID. The node ID is the SHA256 hash of the host key (public key).
        # It is thus 256 bits long. The host key is a 4096 bits key generated with RSA.
        # Public keys are shared out-of-band.
        self.node_id = int(hashlib.sha256(host_key.encode()).hexdigest(), 16)


        self.routing_table_lock = asyncio.Lock()
        self.routing_table : RoutingTable = RoutingTable(self.node_id)
        self.local_hash_table_lock = asyncio.Lock()
        self.local_hash_table : LocalHashTable = LocalHashTable()

    

