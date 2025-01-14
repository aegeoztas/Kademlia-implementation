from collections import deque
from ping import sync_ping_node
from xor_distance import key_distance
from constants import *


class NodeTuple:
    """
    A NodeTuple represent the contact information of peer. It contains the ip, the port and the key id of the peer.
    A NodeTuple is the unit stored in the KBuckets.
    """

    def __init__(self, ip_address: str, port: int, node_id: int):
        """
        The constructor of a NodeTuple
        :param ip_address: (str) The ip address of the remote peer.
        :param port: (int) The port of the remote peer.
        :param node_id:(int) The id (key) of the peer.
        """

        # Validation of the parameters
        if port < 0 or port > MAX_PORT_NUMBER:
            raise ValueError(f"Port must be between 0 and {MAX_PORT_NUMBER}")
        if node_id < 0:
            raise ValueError("Node ID must be greater than or equal to zero.")
        if node_id > MAX_KEY_VALUE:
            raise ValueError("Node ID must be in the key space range.")

        self.ip_address = ip_address
        self.port = port
        self.node_id = node_id

    def __eq__(self, other):
        """
        Override of the method equal. The equality is defined by with the equality of the node_id.
        :param other: another NodeTuple
        :return: true if the components of both NodeTuples are equals.
        """
        return self.node_id == other.node_id

    def __str__(self):
        """
        Override of the method __str__. Used for testing.
        :return: A string representation of the NodeTuple.
        """
        return f"Node Tuple information [ Node ID: {self.node_id}, port: {self.port}, IP: {self.ip_address} ]"

    def __hash__(self):
        """
        Override of the method __hash__.
        :return: a hash of the NodeTuple.
        """
        return hash(self.node_id)

    def key_distance_to(self, key: int) -> int:
        """
        This method returns the xor distance (int) between the id of the peer and the key passed in parameters.
        :param key: The key to compute the distance with.
        :return: The xor distance (int)
        """
        return key_distance(self.node_id, key)

    @staticmethod
    def node_id_binary_representation(node_id: int) -> str:
        """
        This method is used to obtain the binary representation of the node id.
        :param node_id: A node ID in integer representation.
        :return: The node ID in binary representation stored in a string.
        """
        return format(node_id, f'0{KEY_BIT_LENGTH}b')

    @staticmethod
    def has_prefix(key: int, prefix: str)->bool:
        """
        The method has_prefix returns true if the id matches the prefix
        :param key: the key of the node or the distance (int)
        :param prefix: the prefix (str)
        """
        return NodeTuple.node_id_binary_representation(key).startswith(prefix)


class KBucket:
    """
    A K-Bucket contains the information of at most K peers. All nodes contained
    in the K-Bucket must have their id matching the bucket_prefix. The bucket prefix therefore
    represent the bucket identity.

    The nodes are stored in a queue data structure. The most recently seen Node is placed at the head of the queue and
    the least recently seen node is at the tail.
    """

    def __init__(self, local_node:NodeTuple,  bucket_prefix: str):
        """
        The constructor of a KBucket.
        :param local_node: contains ip, port and id of the local node.
        :param bucket_prefix: the prefix of IDs of the nodes contained in the bucket.
        """
        self.local_node: NodeTuple = local_node

        self.bucket_prefix: str = bucket_prefix
        # size represent the number of nodes that we have currently in the bucket
        self.size: int = 0
        # bucket is the array that contains the triples (ip, port, id) that represents the nodes in the bucket
        self.bucket: deque[NodeTuple] = deque()

    def update_bucket(self, candidate_node: NodeTuple):
        """
        The purpose of the method update_bucket is to update the content of the bucket
        with the information of a specific peer.
        :param candidate_node: The information of the peer: ip_address, port and node_id
        """

        # # Verification of the parameters
        # if not NodeTuple.has_prefix(candidate_node.node_id, self.bucket_prefix):
        #     raise ValueError("Attempted to insert peer information into a bucket with the wrong prefix.")

        # Update of the bucket content:

        # Case 1: if the node is already in the bucket, it is placed at the head of
        # the queue.
        if candidate_node in self.bucket:
            self.bucket.remove(candidate_node)
            self.bucket.appendleft(candidate_node)

        # If the node is not in the bucket, an insertion attempt is performed.
        else:

            # Case 2: if the bucket is not full, we add the new node.
            if self.size < K:
                self.bucket.appendleft(candidate_node)
                self.size += 1

            # Case 3: if the bucket is full, we ping the last node. If it does not respond we replace it.
            # If the last node respond to the ping we place it at the start of the list.
            else:
                last_node = self.bucket.pop()
                positive_response = sync_ping_node(self.local_node.ip_address,
                                                   self.local_node.port,
                                                   self.local_node.node_id,
                                                   remote_ip=last_node.ip_address,
                                                   remote_port=last_node.port)
                if positive_response:
                    self.bucket.appendleft(last_node)
                else:
                    self.bucket.appendleft(candidate_node)

    def is_full(self) -> bool:
        """
        The method is_full returns true if the bucket is full and false otherwise.
        """
        return self.size == K

    def __contains__(self, item : NodeTuple)-> bool:
        """
        Override of the method contains,  returns true if the bucket contains the specific node information and false otherwise.
        """
        return self.bucket.__contains__(item)

    def get_peers(self) -> deque[NodeTuple]:
        """
        The method get_peers returns the queue containing the information of the nodes.
        """
        return self.bucket

    def __str__(self):
        """
        Override of the method __str__. Used for testing.
        :return: a string representation of the KBucket with its content
        """
        value =  f"K-Bucket information [ Prefix: \"{self.bucket_prefix}\" Size: {self.size} ] "
        value += "\nContent: "
        for i, node in enumerate(self.bucket):
            value += f"\n#{i}\t{node}"

        return value

class ComparableNodeTuple:
    # This class is used to compare two NodeTuple. A NodeTuple with a smaller distance to a specific key
    # is considered greater than the other with a bigger distance.

    def __init__(self, node_tuple: NodeTuple, reference_key: int):
        self.nodeTuple: NodeTuple = node_tuple
        self.reference_key: int = reference_key

    def __lt__(self, other):
        # Nodes are compared with distance

        return key_distance(self.nodeTuple.node_id, self.reference_key) < key_distance(other.nodeTuple.node_id,
                                                                                       self.reference_key)

