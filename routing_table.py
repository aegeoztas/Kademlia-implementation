import math
import os

from abc import ABC, abstractmethod
from collections import deque

from dotenv import load_dotenv

from xor_distance import key_distance
from k_bucket import KBucket, NodeTuple

# Load .env file, useful for testing purpose.
load_dotenv()

# Global variables
MAX_PORT_NUMBER = 65535
KEY_BIT_LENGTH = int(os.getenv("KEY_BIT_LENGTH")) # The number of bit in a key
MAX_KEY_VALUE = int(math.pow(2, KEY_BIT_LENGTH)) - 1  # The maximum value a key of an object or node id can have
K = int(os.getenv("K")) # The capacity of one single K-Bucket

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
        """
        Constructor of a TreeNode.
        :param host_key: The id key of the local peer. It is a KEY_BIT_LENGTH bits key that represent the identity of
        the node. This value is invariant in the whole tree.
        :param prefix: The prefix associated with the TreeNode. Every node contained in the subtree of the node has its ID matching
        the
        """
        if host_key < 0 or host_key > MAX_KEY_VALUE:
            raise ValueError("Invalid host_key")

        self.host_key: int = host_key
        self.prefix: str = prefix

    @abstractmethod
    def update(self, new_peer: NodeTuple):
        """
        The update method is a recursive method that update the routing table with the information of a peer.
        """
        pass

    @abstractmethod
    def get_nearest_peers(self, distance: int, nb_of_peers) -> list[NodeTuple]:
        """
        The method get_nearest_peers is a recursive function that returns the n peers that have their value of
        distance the closest to the value distance given as parameter.
        """
        pass

    # TODO check
    # @abstractmethod
    # def get_node_bucket(self, node_key: int) :
    #     """
    #     The method get_node is a recursive function that returns node object with the given key
    #     by recursively search it.
    #     """
    #     pass

class InternalNode(TreeNode):
    """
    An internal node does not contain itself peer information's and hence does not contain a K-Bucket.
    However, it defines a subtree that contains all peers whose distance in binary notation matches its prefix.
    """

    def __init__(self, host_key: int = None, prefix: str = None, left: TreeNode = None, right: TreeNode = None):
        """
        Constructor of an InternalNode.
        :param host_key: The ID of the local node.
        :param prefix: The prefix that matches all node IDs present in the subtree.
        :param left: The left subtree of the internal node.
        :param right: The right subtree of the internal node.
        """
        super().__init__(host_key, prefix)
        self.left: TreeNode = left
        self.right: TreeNode = right

    def update(self, new_peer: NodeTuple):
        """
        As an internal node does not contain a K-Bucket, the method update will recursively call the update method
        of the right or left child depending on the prefix of the distance of the node.
        """

        # Verification that the distance of the peer matches the prefix of the node.
        if not NodeTuple.has_prefix(new_peer.key_distance_to(self.host_key), self.prefix):
            raise ValueError("The node should not be inserted in this subtree because the binary representation \
            of the distance does not match the prefix of the subtree")

        right_prefix: str = self.prefix + "0"

        # If the peer prefix matches the prefix of the right child we call the update method of the right child.
        # Otherwise, the method of the left child is called.
        if NodeTuple.has_prefix(new_peer.key_distance_to(self.host_key), right_prefix):
            self.right.update(new_peer)
        else:
            self.left.update(new_peer)

    def get_nearest_peers(self, distance: int, nb_of_peers) -> list[NodeTuple]:
        """
        The method get_nearest_peers called on an internal node will recursively call the same method on the children
        with the appropriate distance prefix. If the number of peers returned by the children is smaller than the number
        asked, it will ask its other children to returns the remaining closest peers.
        """

        # If the distance given in parameter matches the prefix of the right children, the method of the right children
        # is called.
        if NodeTuple.has_prefix(distance, self.right.prefix):
            peers: list[NodeTuple] = self.right.get_nearest_peers(distance, nb_of_peers)
            # If the number of peers is not sufficient, the left children is asked to return the other closest peers.
            nb_of_received_peers = len(peers)
            if nb_of_received_peers < nb_of_peers:
                # Computation of the distance that will be used as parameter for the call on the left children.
                # This is required for getting the peers in the right order and to avoid an error.
                distance_for_left_bucket = int((self.right.prefix[:-1] + "1").ljust(KEY_BIT_LENGTH, "0"), 2)
                peers_from_left: list[NodeTuple] = self.left.get_nearest_peers(distance_for_left_bucket,
                                                                               nb_of_peers - nb_of_received_peers)
                # The peers from the left children are added at the tail of the list of peers
                peers.extend(peers_from_left)
            return peers

        # The case for the left children is symmetric.
        else:
            peers: list[NodeTuple] = self.left.get_nearest_peers(distance, nb_of_peers)
            nb_of_received_peers = len(peers)
            if nb_of_received_peers < nb_of_peers:
                distance_for_right_bucket = int(("0" + self.left.prefix).ljust(KEY_BIT_LENGTH, "1"), 2)
                peers_from_right: list[NodeTuple] = self.right.get_nearest_peers(distance_for_right_bucket,
                                                                                 nb_of_peers - nb_of_received_peers)
                peers.extend(peers_from_right)
            return peers

    # def get_node_bucket(self, node_key: int):
    #     """
    #     As an internal node does not contain a K-Bucket, the method get_node_bucket will recursively call the get_node_bucket method
    #     of the right or left child depending on the prefix of the distance of the node.
    #     """
    #
    #     if not has_prefix(key_distance(node_key,self.host_key), self.prefix):
    #         raise ValueError("The node should not be searched for in this subtree because the binary representation \
    #                of the distance does not match the prefix of the subtree")
    #
    #     right_prefix: str = self.prefix + "0"
    #
    #     # If the peer prefix matches the prefix of the right child we call the get_node method of the right child.
    #     # Otherwise, the method of the left child is called.
    #     if has_prefix(key_distance(node_key,self.host_key), right_prefix):
    #         self.right.get_node_bucket(node_key)
    #     else:
    #         self.left.get_node_bucket(node_key)
class Leaf(TreeNode):
    """
    All leaf nodes contain a K-Bucket that stores the information of the peers whose distance
    matches the prefix of the bucket.
    """

    def __init__(self, host_key: int, prefix: str):
        """
        Constructor of a LeafNode.
        :param host_key: The ID of the local node.
        :param prefix: The prefix that matches all node IDs present in K-bucket of the Leaf.
        :param bucket: The K-bucket contained in the Leaf.
        """
        super().__init__(host_key, prefix)
        self.bucket: KBucket = KBucket(prefix)

    def update(self, new_peer: NodeTuple):
        """
        The method update called on a leaf will update the content of its K-Bucket. Depending on whether it
        is a right node, i.e. a node having a prefix with only 0's,  or a left node, i.e. a node having a prefix
        with at least one 1, the leaf with the bucket may be split if the bucket is full.
        """
        pass

    def get_nearest_peers(self, distance: int, nb_of_peers) -> list[NodeTuple]:
        """
        The method get_nearest_peers called on a leaf will simply return the content of the bucket. The list of peers
        will be sorted by their closeness to the distance given as parameter. This is required because the peers are
        sorted by most recently seen in the K-Bucket.
        """

        # The content of the bucket is sorted by the closest value to the distance
        k_bucket_content_sorted = sorted(
            self.bucket.get_peers(), key=lambda x: abs(distance - x.key_distance_to(self.host_key)))

        return k_bucket_content_sorted[:nb_of_peers]

    # def get_node_bucket(self,node_key: int):
    #     """
    #     get_node_bucket method will get the leaf at this point if it matches its id
    #     """
    #     if self.host_key != node_key:
    #         raise ValueError("The Leaf does not match the node searched! Query misdirected! ")
    #     else:
    #         return self.bucket


class LeftLeaf(Leaf):
    """
    A left leaf contains a K-Bucket that covers a prefix of distance that contains at least one 1. Depending
     on the height y at which it is located in the tree, it corresponds to the k-bucket containing nodes
     at a distance greater than 2^y. In accordance with the Kademlia protocol, left leaf buckets can not be split.
     This ensures that the local node knows more and more nodes as its distance from them decreases.
    """

    def __init__(self, host_key: int, prefix: str):
        super().__init__(host_key, prefix)

    def update(self, new_peer: NodeTuple):
        """
        The method update called on a left leaf will update its k-bucket content. If the bucket is already full,
        the bucket will not be split and the new peer will either be discarded or replace another peer.
        """
        # Verification that the distance of the peer matches the prefix of the node.
        if not NodeTuple.has_prefix(new_peer.key_distance_to(self.host_key), self.prefix):
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

    def __init__(self, host_key: int, prefix: str, parent=None):
        super().__init__(host_key, prefix)
        self.parent: InternalNode = parent

    def __split_bucket_and_add_new_peer(self, new_peer: NodeTuple):
        """
        This method split the K-Bucket of the leaf and transforms the leaf into an internal node.
        """

        # Creation of two new leaves
        right_leaf_id: str = self.prefix + "0"
        new_right_leaf: RightLeaf = RightLeaf(self.host_key, right_leaf_id, None)
        left_leaf_id: str = self.prefix + "1"
        new_left_leaf: LeftLeaf = LeftLeaf(self.host_key, left_leaf_id)

        # Creation of an internal node that will replace the current Leaf and will be the parent of the new leaves
        new_node = InternalNode(self.host_key, prefix=self.prefix, left=new_left_leaf, right=new_right_leaf)

        # Add the pointers to the parents in the right leaf
        new_right_leaf.parent = new_node

        # Update the pointer of the parent of the current leaf to the new node
        self.parent.right = new_node

        # The elements contained in the bucket of the old leaf are inserted in the two new buckets
        peers: deque[NodeTuple] = self.bucket.get_peers()
        for peer in reversed(peers):

            if NodeTuple.has_prefix(peer.key_distance_to(self.host_key), prefix=new_right_leaf.prefix):
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
        if not NodeTuple.has_prefix(new_peer.key_distance_to(self.host_key), self.prefix):
            raise ValueError("The node should not be inserted in this bucket because the binary representation \
            of the distance does not match the prefix of the bucket")

        # If the bucket is full, we split the bucket into two new buckets
        if ((not new_peer in self.bucket)
                and self.bucket.is_full()
                # The bucket is not split if the maximal number of buckets has been reached.
                and len(self.prefix) < KEY_BIT_LENGTH):

            self.__split_bucket_and_add_new_peer(new_peer)

        # If the bucket is not full, we simply update the bucket with the new peer
        else:
            self.bucket.update_bucket(new_peer)


class TreeRootPointer(InternalNode):
    """
    A TreeRootPointer is a simply a pointer to the root of the tree datastructure that represent the routing table.
    It is technically an InternalNode in order to make it easier to split the root when it's a leaf at the start.
    """

    def __init__(self, host_key: int, prefix: str):
        super().__init__(host_key, prefix)

    def update(self, new_peer: NodeTuple):
        """
        The method update will simply call the update method on the root.
        """
        self.right.update(new_peer)

    def set_root(self, root: TreeNode):
        self.right = root

    def get_root(self):
        return self.right

    def get_nearest_peers(self, distance: int, nb_of_peers) -> list[NodeTuple]:
        """
        The method get_nearest_peers called on a root pointer will simply call the method of the root.
        """
        return self.right.get_nearest_peers(distance, nb_of_peers)

    # def get_node_bucket(self,node_key: int):
    #     """
    #     The method get_nearest_peers called on a root pointer will simply call the method of the root.
    #     """
    #     return self.right.get_node_bucket(node_key)

class RoutingTable:
    """
    The routing table contains the contact information of the other peers. It uses the dynamic tree data structure
    previously defined. Peer data are placed in the tree according to their xor key distance from the host key.
    """

    def __init__(self, host_key: int):
        """
        The host key is the key of the local node.
        At the start, the tree consists only of one leaf that contains a K-bucket that covers the entire distance
        prefix range.
        """
        self.host_key: int = host_key
        self.root_pointer: TreeRootPointer = TreeRootPointer(host_key, "")
        root: TreeNode = RightLeaf(host_key, "", self.root_pointer)
        self.root_pointer.set_root(root)

    def update_table(self, ip_address: str, port: int, node_id: int):
        """
        The method update_table is called each time that the local peer receive a message from the network. It updates
        the routing table information with the contact details of the sender and in accordance with the kademlia
        protocol.
        """

        # Verification that the parameters are valid
        if port < 0 or port > MAX_PORT_NUMBER:
            raise ValueError(f"Port must be between 0 and {MAX_PORT_NUMBER}")
        if node_id < 0:
            raise ValueError("Node ID must be greater than or equal to zero.")
        if node_id > MAX_KEY_VALUE:
            raise ValueError("Node ID must be in the key space range.")

        # As the data structure store NodeTuple's, it is needed to create one for the sender information
        new_peer = NodeTuple(ip_address, port, node_id)

        # The update method is called on the root and the modification will be done recursively on the tree.
        self.root_pointer.get_root().update(new_peer)

    def get_nearest_peers(self, key: int, nb_of_peers) -> list[NodeTuple]:
        """
        The method get_nearest_peers returns the information of the n closest peer to the key value given as parameter.
        If there is less than n peers in the routing table, all peers will be returned.
        """
        return self.root_pointer.get_nearest_peers(key_distance(self.host_key, key), nb_of_peers)

    # def get_host_bucket(self):
    #     """
    #     The method get_host_bucket returns the bucketof the host node/leaf with the host key as its routing key.
    #
    #     """
    #     return self.root_pointer.get_node_bucket(self.host_key)

