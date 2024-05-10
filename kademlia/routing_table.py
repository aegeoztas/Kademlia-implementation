from abc import ABC, abstractmethod
from collections import deque

from k_bucket import KBucket, NodeTriple

K = 4


class Tree(ABC):
    pass


class TreeNode(Tree):
    def __init__(self, left: Tree, right: Tree):
        self.left = left
        self.right = right


def has_prefix(node_id: int, prefix: str):
    return NodeTriple.node_id_binary_representation(node_id).startswith(prefix)


class TreeLeaf(Tree):
    @abstractmethod
    def update_bucket(self, ip_address: str, port: int, node_id: int):
        pass


class TreeLeftLeaf(TreeLeaf):
    def __init__(self, bucket: KBucket, bucket_id: str):
        self.bucket = bucket
        self.bucket_id = bucket_id

    def update_bucket(self, ip_address: str, port: int, node_id: int):
        if not has_prefix(node_id, self.bucket_id):
            raise ValueError("node_id does not correspond with bucket id")

        self.bucket.update_bucket(ip_address, port, node_id)


class TreeRightLeaf(TreeLeaf):

    def __init__(self, bucket: KBucket, bucket_id: str, parent: TreeNode = None):
        self.bucket = bucket
        self.bucket_id = bucket_id
        self.parent = parent

    def __split_bucket_and_add_new_peer(self, new_peer: NodeTriple):

        # Creation of two new Leaves
        right_leaf_id: str = self.bucket_id + "1"
        new_right_leaf: TreeRightLeaf = TreeRightLeaf(KBucket(right_leaf_id, K), right_leaf_id)
        left_leaf_id: str = self.bucket_id + "0"
        new_left_leaf: TreeLeftLeaf = TreeLeftLeaf(KBucket(left_leaf_id, K), left_leaf_id)

        # Creation of a Node that will replace the current Leaf and will be the parent of the new leaves
        new_node = TreeNode(left=new_left_leaf, right=new_right_leaf)

        # We add the pointers to the parents in the children
        new_right_leaf.parent = new_node
        new_left_leaf.parent = new_node

        # We update the pointer of the parent of the current leaf to the new node
        # If the current leaf is the root, it does not have a parent
        if not (self.parent is None):
            self.parent.right = new_node

        # The elements contained in the bucket of the old leaf are inserted in the two new buckets
        peers: deque[NodeTriple] = self.bucket.get_peers()
        for peer in reversed(peers):
            if has_prefix(node_id=peer.node_id, prefix=new_right_leaf.bucket_id):
                new_right_leaf.update_bucket(peer.ip_address, peer.port, peer.node_id)
            else:
                new_left_leaf.update_bucket(peer.ip_address, peer.port, peer.node_id)

        # Lastly, add the new peer in the right bucket
        if has_prefix(node_id=new_peer.node_id, prefix=new_right_leaf.bucket_id):
            new_right_leaf.update_bucket(new_peer.ip_address, new_peer.port, new_peer.node_id)
        else:
            new_left_leaf.update_bucket(new_peer.ip_address, new_peer.port, new_peer.node_id)

    def update_bucket(self, ip_address: str, port: int, node_id: int):
        if not has_prefix(node_id, self.bucket_id):
            raise ValueError("node_id does not correspond with bucket id")

        # If the bucket is full, we split the bucket into two new buckets
        if ((not self.bucket.contains(ip_address, port, node_id))
                and self.bucket.is_full()):
            self.__split_bucket_and_add_new_peer(NodeTriple(ip_address, port, node_id))
            return
        # If the bucket is not full, we simply update the bucket with the new peer
        else:
            self.bucket.update_bucket(ip_address, port, node_id)


