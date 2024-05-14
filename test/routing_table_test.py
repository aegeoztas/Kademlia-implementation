from context import kademlia
from kademlia import *
import pytest
import random


def display_table_content(table: RoutingTable):
    print("ID of the table: {}".format(table.host_key))

    done = False
    index = 0

    current_node = table.root_pointer.get_root()
    print("-----------------------------------------")
    print("Level {}: ".format(index))
    while not done:

        if isinstance(current_node, RightLeaf):
            done = True
            print("Right leaf with prefix \"{}\". Bucket has {} elements:".format(current_node.prefix,
                                                                                  current_node.bucket.size))
            for peer in current_node.bucket.get_peers():
                print("\t ip = \"{}\" | port = {} | node_id = {}".format(peer.ip_address, peer.port, peer.node_id))
        else:

            print("Internal node with prefix \"{}\"".format(current_node.prefix))

            index += 1

            left_leaf: LeftLeaf = current_node.left

            print("-----------------------------------------")
            print("Level {}: ".format(index))

            print("Left leaf with prefix \"{}\". Bucket has {} elements:".format(left_leaf.prefix,
                                                                                 left_leaf.bucket.size))
            for peer in left_leaf.bucket.get_peers():
                print("\t ip = \"{}\" | port = {} | node_id = {}".format(peer.ip_address, peer.port, peer.node_id))
            print()
            current_node = current_node.right

        index += 1


def display_list_of_node_tuple(list_of_nodes: list[NodeTuple]):
    for peer in list_of_nodes:
        print("\t ip = \"{}\" | port = {} | node_id = {}".format(peer.ip_address, peer.port, peer.node_id))


def display_tree_test():
    # test works with K = 4 and KEY_LENGTH = 4

    host_key = 0
    table: RoutingTable = RoutingTable(host_key)
    table.update_table("", 0, 0)
    table.update_table("", 0, 1)
    table.update_table("", 0, 2)
    table.update_table("", 0, 8)
    table.update_table("", 0, 9)
    for i in range(3, 6):
        table.update_table("", i, i)
    display_table_content(table)

    list_of_nodes = table.get_nearest_peers(2, 4)
    print("size of list of nearest peer to key 2 = {}".format(len(list_of_nodes)))
    display_list_of_node_tuple(list_of_nodes)


def leaf_get_nearest_peers_test():
    # test get_nearest_peers
    left: LeftLeaf = LeftLeaf(0, "01", KBucket("01"))
    right: RightLeaf = RightLeaf(0, "0", KBucket("0"))
    for i in range(4, 8):
        node = NodeTuple("", i, i)
        left.update(node)
        right.update(node)
    left_list = left.get_nearest_peers(0, 4)
    right_list = right.get_nearest_peers(0, 4)
    for i in range(4, 8):
        node = NodeTuple("", i, i)
        assert (node in left_list and node in right_list)

    # test sorted list
    sorted1 = left.get_nearest_peers(8, 4)
    sorted2 = right.get_nearest_peers(8, 4)
    for i in range(7, 4, -1):
        assert (sorted1.pop(0).node_id == sorted2.pop(0).node_id == i)

    sorted3 = left.get_nearest_peers(0, 4)
    sorted4 = right.get_nearest_peers(0, 4)
    for i in range(4, 8):
        assert (sorted3.pop(0).node_id == sorted4.pop(0).node_id == i)

    sorted5 = left.get_nearest_peers(5, 4)
    sorted6 = right.get_nearest_peers(5, 4)
    assert (sorted5.pop(0).node_id == sorted6.pop(0).node_id == 5)
    assert (sorted5.pop(0).node_id == sorted6.pop(0).node_id == 6)
    assert (sorted5.pop(0).node_id == sorted6.pop(0).node_id == 4)
    assert (sorted5.pop(0).node_id == sorted6.pop(0).node_id == 7)


def left_leaf_test():
    # test works with K = 4 and KEY_LENGTH = 4

    bucket: KBucket = KBucket("100")
    left_leaf: LeftLeaf = LeftLeaf(host_key=0, bucket=bucket, prefix="100")

    # Test update function

    # Leaf should raise error if invalid prefix
    with pytest.raises(ValueError):
        left_leaf.update(NodeTuple("", 0, node_id=0))

    # Test update bucket
    left_leaf: LeftLeaf = LeftLeaf(host_key=0, bucket=bucket, prefix="100")
    node = NodeTuple("", 0, 9)
    left_leaf.update(node)
    assert (left_leaf.bucket.contains(node))


def right_leaf_test():
    # test works with K = 4 and KEY_LENGTH = 4

    bucket: KBucket = KBucket("000")
    right_leaf: RightLeaf = RightLeaf(host_key=0, bucket=bucket, prefix="0")

    # Test update function

    # Leaf should raise error if invalid prefix
    with pytest.raises(ValueError):
        right_leaf.update(NodeTuple("", 0, node_id=8))

    # Test update with not full bucket
    parent: InternalNode = InternalNode()
    right_leaf: RightLeaf = RightLeaf(host_key=0, bucket=bucket, prefix="0", parent=parent)
    parent.right = right_leaf
    for i in range(4, 8):
        right_leaf.update(NodeTuple("", i, i))

    for i in range(4, 8):
        assert (right_leaf.bucket.contains(NodeTuple("", i, i)))

    # Test update with full bucket

    assert (isinstance(parent.right, RightLeaf))
    right_leaf.update(NodeTuple("", 3, 3))
    created_internal_node = parent.right
    # Test split bucket
    assert (isinstance(created_internal_node, InternalNode))
    for i in range(4, 8):
        # The nodes 4-7 should be in the bucket of the left children
        assert (created_internal_node.left.bucket.contains(NodeTuple("", i, i)))
    # the node 3 should be in the bucket of the right children
    assert (created_internal_node.right.bucket.contains(NodeTuple("", 3, 3)))


def internal_node_test():
    right = RightLeaf(0, "0", KBucket("0"))
    left = LeftLeaf(0, "1", KBucket("1"))
    internal_node = InternalNode(0, "", left, right)
    right.parent = internal_node

    # test update
    for i in range(0, 4):
        internal_node.update(NodeTuple("", i, i))
    for i in range(8, 12):
        internal_node.update(NodeTuple("", i, i))
    for i in range(0, 4):
        internal_node.right.bucket.contains(NodeTuple("", i, i))
    for i in range(8, 12):
        internal_node.left.bucket.contains(NodeTuple("", i, i))

    # test get_nearest_peers
    # We also test the order of the elements
    four_element_right = internal_node.get_nearest_peers(0, 4)
    for i in range(0, 4):
        assert (four_element_right.pop(0).node_id == i)

    four_element_right = internal_node.get_nearest_peers(5, 4)
    for i in range(3, -1, -1):
        assert (four_element_right.pop(0).node_id == i)

    four_element_left = internal_node.get_nearest_peers(8, 4)
    for i in range(8, 12):
        assert (four_element_left.pop(0).node_id == i)

    four_element_left = internal_node.get_nearest_peers(15, 4)
    for i in range(11, 7, -1):
        assert (four_element_left.pop(0).node_id == i)


def routing_table_test_with_chosen_values():
    # test works with K = 4 and KEY_LENGTH = 4 and dummy ping that returns always true
    local_node_key = 0

    table: RoutingTable = RoutingTable(host_key=local_node_key)

    for i in range(0, 16):
        table.update_table(ip_address="", port=i, node_id=i)

    display_table_content(table)

    # Test get_nearest_peers with bucket contents
    for i in range(0, 4):
        right_leaf_bucket_00 = table.get_nearest_peers(i, 4)
        for j in range(0, 4):
            assert (NodeTuple("", j, j) in right_leaf_bucket_00)

    for i in range(8, 12):
        left_bucket_1 = table.get_nearest_peers(i, 4)
        for j in range(8, 12):
            assert (NodeTuple("", j, j) in left_bucket_1)

    for i in range(4, 8):
        left_bucket_01 = table.get_nearest_peers(i, 4)
        for j in range(4, 8):
            assert (NodeTuple("", j, j) in left_bucket_01)

    # Test with nb_of_peers > K

    # left side
    peers = table.get_nearest_peers(0, 8)
    for i in range(0, 8):
        assert (NodeTuple("", i, i) in peers)
    # Test of the order
    for i in range(0, 8):
        assert (peers.pop(0).node_id == i)

    # right side
    peers = table.get_nearest_peers(4, 8)
    for i in range(0, 8):
        assert (NodeTuple("", i, i) in peers)
    # Test of the order
    for i in range(4, 8):
        assert (peers.pop(0).node_id == i)
    for i in range(3, -1, -1):
        assert (peers.pop(0).node_id == i)


def routing_table_test_with_random_values():
    # test works with K = 4 and KEY_LENGTH = 4 and dummy ping that returns always true
    local_node_id = random.randint(0, 16)

    table: RoutingTable = RoutingTable(local_node_id)

    # Filling of the table
    random_peers = [random.randint(0, 16) for _ in range(4)]
    for element in random_peers:
        table.update_table("", element, element)

    # Test get all peers
    retrieved_nodes = table.get_nearest_peers(random.randint(0, 16), 4)
    for element in random_peers:
        assert (NodeTuple("", element, element) in retrieved_nodes)

    # Test get each peer
    for element in random_peers:
        assert (NodeTuple("", element, element).__eq__(table.get_nearest_peers(element, 1).pop(0)))


# display_tree_test()
right_leaf_test()
leaf_get_nearest_peers_test()
internal_node_test()
routing_table_test_with_chosen_values()
routing_table_test_with_random_values()
