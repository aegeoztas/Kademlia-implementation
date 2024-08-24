import hashlib
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from LocalHashTable import *
from routing_table import *



class LocalNode:
    """
    This class represents the node linked to the instance of this program.
     It essentially contains the node's routing table and the node's storage.
    """

    def __init__(self, ip : str, port: int, host_key:bytes = None):
        self.ip: str = ip
        self.port: int = port

        if host_key is None:
            host_key = self.generate_random_rsa_key()
        # Creation of the node ID. The node ID is the SHA256 hash of the host key (public key).
        # It is thus 256 bits long. The host key is a 4096 bits key generated with RSA.
        # Public keys are shared out-of-band.
        self.node_id = int(hashlib.sha256(host_key).hexdigest(), 16)

        self.routing_table : RoutingTable = RoutingTable(self.node_id)
        self.local_hash_table : LocalHashTable = LocalHashTable()


    @staticmethod
    def generate_random_rsa_key() -> bytes:
        """
        Generates a random  RSA key and returns the public key as bytes
        In case there isn't a key provided.
        """
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096
        )
        public_key = private_key.public_key()

        # Serialize the public key to bytes
        public_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return public_key_bytes