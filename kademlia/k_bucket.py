import math
from collections import deque

from kademlia.dummy import ping_node
from .distance import KEY_LENGTH

MAX_PORT_NUMBER = 65535
MAX_KEY_VALUE = math.pow(2, KEY_LENGTH)  # The maximum value a key of an object or node id can have
K = 4  # The capacity of one single K-Bucket


class NodeTuple:
    """
    A NodeTuple represent the contact information of peer. It contains the ip, the port and the key id of the peer.
    A NodeTuple is the unit stored in the KBuckets.
    """

    def __init__(self, ip_address: str, port: int, node_id: int):

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
        return self.ip_address == other.ip_address and self.port == other.port and self.node_id == other.node_id

    @staticmethod
    def node_id_binary_representation(node_id: int) -> str:
        """
        This method is used to obtain the binary representation of the node id.
        :param node_id: A node ID in integer representation.
        :return: The node ID in binary representation stored in a string.
        """
        return format(node_id, f'0{KEY_LENGTH}b')


class KBucket:
    """
    A K-Bucket contains the information of at most K peers. All nodes contained
    in the K-Bucket must have their id matching the bucket_prefix. The bucket prefix therefore
    represent the bucket id.

    The nodes are stored in a queue data structure. The most recently seen Node is the head of the queue and
    the least recently seen node is at the tail.
    """

    def __init__(self, bucket_prefix: str):

        # bucket_prefix is the prefix of IDs of the nodes contained in the bucket.
        self.bucket_prefix: str = bucket_prefix
        # size represent the number of nodes that we have currently in the bucket
        self.size: int = 0
        # bucket is the array that contains the triples (ip, port, id) that represents the nodes in the bucket
        self.bucket: deque[NodeTuple] = deque()

    def update_bucket(self, ip_address: str, port: int, node_id: int):
        """
        The purpose of the method update_bucket is to update the content of the bucket
        with the information of a specific peer.
        :param ip_address: The ip address of the peer
        :param port: The port of the peer
        :param node_id: The node_id of the peer
        """

        # Validation of the parameters
        if port < 0 or port > MAX_PORT_NUMBER:
            raise ValueError(f"Port must be between 0 and {MAX_PORT_NUMBER}")
        if node_id < 0:
            raise ValueError("Node ID must be greater than or equal to zero.")
        if node_id > MAX_KEY_VALUE:
            raise ValueError("Node ID must be in the key space range.")

        # The node involved in the update
        candidate_node: NodeTuple = NodeTuple(ip_address, port, node_id)

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
                self.bucket.appendleft(NodeTuple(ip_address, port, node_id))
                self.size += 1

            # Case 3: if the bucket is full, we ping the last node. If it does not respond we replace it.
            # If the last node respond to the ping we place it at the start of the list.
            else:
                last_node = self.bucket.pop()
                positive_response = ping_node(last_node.ip_address, last_node.port, last_node.node_id)
                if positive_response:
                    self.bucket.appendleft(last_node)
                else:
                    self.bucket.appendleft(NodeTuple(ip_address, port, node_id))

    def is_full(self) -> bool:
        """
        The method is_full returns true if the bucket is full and false otherwise.
        :return:
        """
        return self.size == K

    def contains(self, ip_address: str, port: int, node_id: int) -> bool:
        """
        The method contains returns true if the bucket contains the specific node information and false otherwise.
        """
        return self.bucket.__contains__(NodeTuple(ip_address, port, node_id))

    def get_peers(self) -> deque[NodeTuple]:
        """
        The method get_peers returns the queue containing the information of the nodes.
        """
        return self.bucket
