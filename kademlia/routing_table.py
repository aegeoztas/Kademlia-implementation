from abc import ABC, abstractmethod
from collections import deque

from .distance import KEY_LENGTH
from .k_bucket import KBucket, NodeTuple, has_prefix, MAX_PORT_NUMBER, MAX_KEY_VALUE


class TreeNode(ABC):
    """
    The abstract object TreeNode is the basis for the dynamic tree datastructure that represent the routing table.
    A TreeNode can either be an internal node or a leaf that store a K-Bucket.

    The host_key is the id key of the local peer.

    Peer data are placed in the tree according to their key distance from the host key.

    Each peer stored in the subtree has its distance from the host key, in binary representation,
    matched with the TreeNode prefix.
    """

    def __init__(self, host_key: int, prefix: str):
        self.host_key: int = host_key
        self.prefix: str = prefix

    @abstractmethod
    def update(self, new_peer: NodeTuple):
        """
        The update method is a recursive method that update the routing table with the information of a peer.
        """
        pass


class InternalNode(TreeNode):
    """
    An internal node does not contain itself peer information's and hence does not contain a K-Bucket.
    However, it defines a subtree that contains all peers whose distance in binary notation matches its prefix.
    """
    def __init__(self, host_key: int = None, prefix: str = None, left: TreeNode = None, right: TreeNode = None):
        super().__init__(host_key, prefix)
        self.left: TreeNode = left
        self.right: TreeNode = right

    def update(self, new_peer: NodeTuple):
        """
        As an internal node does not contain a K-Bucket, the method update will recursively call the update method
        of the right or left child depending on the prefix of the distance of the node.
        """

        # Verification that the distance of the peer matches the prefix of the node.
        if not has_prefix(new_peer.key_distance_to(self.host_key), self.prefix):
            raise ValueError("The node should not be inserted in this subtree because the binary representation \
            of the distance does not match the prefix of the subtree")

        right_prefix: str = self.prefix + "0"

        # If the peer prefix matches the prefix of the right child we call the update method of the right child.
        # Otherwise, the method of the left child is called.
        if has_prefix(new_peer.key_distance_to(self.host_key), right_prefix):
            self.right.update(new_peer)
        else:
            self.left.update(new_peer)


class Leaf(TreeNode):
    """
    All leaf nodes contain a K-Bucket that stores the information of the peers whose distance
    matches the prefix of the bucket.
    """

    def __init__(self, host_key: int, prefix: str,  bucket: KBucket):
        super().__init__(host_key, prefix)
        self.bucket: KBucket = bucket

    def update(self, new_peer: NodeTuple):
        """
        The method update called on a leaf will update the content of its K-Bucket. Depending on whether it
        is a right node, i.e. a node having a prefix with only 0's,  or a left node, i.e. a node having a prefix
        with at least one 1, the leaf with the bucket may be split if the bucket is full.
        """
        pass


class LeftLeaf(Leaf):
    """
    A left leaf contains a K-Bucket that covers a prefix of distance that contains at least one 1. Depending
     on the height y at which it is located in the tree, it corresponds to the k-bucket containing nodes
     at a distance greater than 2^y. In accordance with the Kademlia protocol, left leaf buckets can not be split.
     This ensures that the local node knows more and more nodes as its distance from them decreases.
    """

    def __init__(self, host_key: int, prefix: str, bucket: KBucket):
        super().__init__(host_key, prefix, bucket)

    def update(self, new_peer: NodeTuple):
        """
        The method update called on a left leaf will update its k-bucket content. If the bucket is already full,
        the bucket will not be split and the new peer will either be discarded or replace another peer.
        """
        # Verification that the distance of the peer matches the prefix of the node.
        if not has_prefix(new_peer.key_distance_to(self.host_key), self.prefix):
            raise ValueError("The node should not be inserted in this bucket because the binary representation \
            of the distance does not match the prefix of the bucket")

        # The K-bucket content is updated.
        self.bucket.update_bucket(new_peer)


class RightLeaf(Leaf):
    """
    A right leaf contains a K-Bucket that covers a prefix of distance that contains only 0's. When trying to add a peer
    in a right leaf bucket that is already full, the leaf becomes and internal node and its bucket is split into two new
    buckets that are attributed to its children.
    """

    def __init__(self, host_key: int,prefix: str, bucket: KBucket, parent=None):
        super().__init__(host_key, prefix, bucket)
        self.parent: InternalNode = parent

    def __split_bucket_and_add_new_peer(self, new_peer: NodeTuple):
        """
        This method split the K-Bucket of the leaf and transforms the leaf into an internal node.
        """

        # Creation of two new leaves
        right_leaf_id: str = self.prefix + "0"
        new_right_leaf: RightLeaf = RightLeaf(self.host_key, right_leaf_id, KBucket(right_leaf_id), None)
        left_leaf_id: str = self.prefix + "1"
        new_left_leaf: LeftLeaf = LeftLeaf(self.host_key, left_leaf_id, KBucket(left_leaf_id))

        # Creation of an internal node that will replace the current Leaf and will be the parent of the new leaves
        new_node = InternalNode(self.host_key, prefix=self.prefix, left=new_left_leaf, right=new_right_leaf)

        # Add the pointers to the parents in the right leaf
        new_right_leaf.parent = new_node

        # Update the pointer of the parent of the current leaf to the new node

        # The elements contained in the bucket of the old leaf are inserted in the two new buckets
        peers: deque[NodeTuple] = self.bucket.get_peers()
        for peer in reversed(peers):

            if has_prefix(peer.key_distance_to(self.host_key), prefix=new_right_leaf.prefix):
                new_right_leaf.update(peer)
            else:
                new_left_leaf.update(peer)

        # Lastly, add the new peer in the right bucket
        new_node.update(new_peer)

    def update(self, new_peer: NodeTuple):
        """
        The method update called on a right leaf will simply update its k-bucket content if it is not full. If it is
        full, the bucket will be split into two new buckets with longer prefix. The bucket is not split if the maximal
        number of buckets has been reached, i.e. the current bucket has a prefix of the key length.
        """

        # Verification that the distance of the peer matches the prefix of the node.
        if not has_prefix(new_peer.key_distance_to(self.host_key), self.prefix):
            raise ValueError("The node should not be inserted in this bucket because the binary representation \
            of the distance does not match the prefix of the bucket")

        # If the bucket is full, we split the bucket into two new buckets
        if ((not self.bucket.contains(new_peer))
                and self.bucket.is_full()
                # The bucket is not split if the maximal number of buckets has been reached.
                and len(self.prefix) < KEY_LENGTH):

            self.__split_bucket_and_add_new_peer(new_peer)

        # If the bucket is not full, we simply update the bucket with the new peer
        else:
            self.bucket.update_bucket(new_peer)


class TreeRootPointer(InternalNode):
    """
    A TreeRootPointer is a simply a pointer to the root of the tree datastructure that represent the routing table.
    It is technically an InternalNode in order to make it easier to split the root when it's a leaf at the start.
    """
    def __init__(self):
        super().__init__()

    def update(self, new_peer: NodeTuple):
        self.right.update(new_peer)

    def set_root(self, root: TreeNode):
        self.right = root

    def get_root(self):
        return self.right


class RoutingTable:

    def __init__(self, host_key: int):
        self.host_key = host_key
        k_bucket: KBucket = KBucket("")
        self.root_container = TreeRootPointer()
        root: TreeNode = RightLeaf(host_key, "", k_bucket, self.root_container)
        self.root_container.set_root(root)

    def update_table(self, ip_address: str, port: int, node_id: int):

        # Verification that the parameters are valid
        if port < 0 or port > MAX_PORT_NUMBER:
            raise ValueError(f"Port must be between 0 and {MAX_PORT_NUMBER}")
        if node_id < 0:
            raise ValueError("Node ID must be greater than or equal to zero.")
        if node_id > MAX_KEY_VALUE:
            raise ValueError("Node ID must be in the key space range.")

        new_peer = NodeTuple(ip_address, port, node_id)

        self.root_container.get_root().update(new_peer)
