import hashlib
import asyncio

from cryptography.hazmat.primitives import serialization

from local_hash_table import *
from routing_table import *



class LocalNode:
    """
    This class represents the node linked to the instance of this program.
     It essentially contains the node's routing table and the node's storage.
    """

    def __init__(self, ip : str, port: int, host_key):

        self.handler_ip: str = ip
        self.handler_port: int = port


        # Creation of the node ID. The node ID is the SHA256 hash of the host key.
        # It is thus 256 bits long.
        # Serialization of  the public key
        pem_public_key = host_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        # Compute the SHA-256 hash of the public key
        sha256_hash = hashlib.sha256(pem_public_key).hexdigest()

        self.node_id = int(sha256_hash, 16)

        self.local_information: NodeTuple = NodeTuple(self.handler_ip, self.handler_port, self.node_id)

        self.routing_table_lock = asyncio.Lock()
        self.routing_table : RoutingTable = RoutingTable(self.local_information)
        self.local_hash_table_lock = asyncio.Lock()
        self.local_hash_table : LocalHashTable = LocalHashTable()

    

