from collections import deque

from kademlia.dummy import ping_node

KEY_LENGTH = 160

class NodeTriple:
    def __init__(self, ip_address: str, port: int, node_id: int):

        if port < 0:
            raise ValueError("Port must be greater than or equal to zero.")
        if node_id < 0:
            raise ValueError("Node ID must be greater than or equal to zero.")

        self.ip_address = ip_address
        self.port = port
        self.node_id = node_id

    def __eq__(self, other):
        return self.ip_address == other.ip_address and self.port == other.port and self.node_id == other.node_id

    @staticmethod
    def node_id_binary_representation(node_id: int) -> str:
        return format(node_id, f'0{KEY_LENGTH}b')


class KBucket:

    def __init__(self, bucket_id: str, k: int):

        if k < 0:
            raise ValueError("Invalid k")
        # bucket_id is the id of the bucket, should be 0 < id < MAX_BUCKET_ID
        self.bucket_id: str = bucket_id
        # k represent the capacity of the bucket
        self.k: int = k
        # size represent the number of nodes that we have currently in the bucket
        self.size: int = 0
        # bucket is the array that contains the triples (ip, port, id) that represents the nodes in the bucket
        self.bucket: deque[NodeTriple] = deque()

    def add_node(self, ip_address: str, port: int, node_id: int):
        # Validation of parameters not necessary as they are verified in
        # update_bucket

        # If the bucket is not full, we add the new node.
        if self.size < self.k:
            self.bucket.appendleft(NodeTriple(ip_address, port, node_id))
            self.size += 1
        # If the bucket is full, we ping the last node. If it does not respond we replace it.
        # If the last node respond to the ping we place it at the start of the list.
        else:
            last_node = self.bucket.pop()
            positive_response = ping_node(last_node.ip_address, last_node.port, last_node.node_id)
            if positive_response:
                self.bucket.appendleft(last_node)
            else:
                self.bucket.appendleft(NodeTriple(ip_address, port, node_id))

    def update_bucket(self, ip_address: str, port: int, node_id: int):
        # Validation of the parameters
        if port < 0:
            raise ValueError("Port must be greater than zero.")
        if node_id < 0:
            raise ValueError("Node ID must be greater than zero.")

        # The node involved in the update
        candidate_node: NodeTriple = NodeTriple(ip_address, port, node_id)

        # If the node is already in the bucket, it is placed at the head of
        # the queue.
        if candidate_node in self.bucket:
            self.bucket.remove(candidate_node)
            self.bucket.appendleft(candidate_node)
        # If the node is not in the bucket, an insertion attempt is performed.
        else:
            self.add_node(ip_address, port, node_id)

    def is_full(self) -> bool:
        return self.size == self.k

    def contains(self, ip_address: str, port: int, node_id: int) -> bool:
        return self.bucket.__contains__(NodeTriple(ip_address, port, node_id))

    def get_peers(self) -> deque[NodeTriple]:
        return self.bucket
