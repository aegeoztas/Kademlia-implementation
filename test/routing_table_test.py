from context import kademlia
from kademlia import *
import pytest


def display_table_content(table: RoutingTable):
    print("ID of the table: {}".format(table.host_key))

    done = False
    index = 0
    current_node = table.root_container.get_root()

    print("-----------------------------------------")
    print("Level {}: ".format(index))
    while not done:

        if isinstance(current_node, RightLeaf):
            done = True
            print("Right leaf with prefix \"{}\". Bucket has {} elements:".format(current_node.bucket_prefix,
                                                                                  current_node.bucket.size))
            for peer in current_node.bucket.get_peers():
                print("\t ip = \"{}\" | port = {} | node_id = {}".format(peer.ip_address, peer.port, peer.node_id))
        else:

            print("Internal node with prefix \"{}\"".format(current_node.prefix))

            index += 1

            left_leaf: LeftLeaf = current_node.left

            print("-----------------------------------------")
            print("Level {}: ".format(index))

            print("Left leaf with prefix \"{}\". Bucket has {} elements:".format(left_leaf.bucket_prefix,
                                                                                 left_leaf.bucket.size))
            for peer in left_leaf.bucket.get_peers():
                print("\t ip = \"{}\" | port = {} | node_id = {}".format(peer.ip_address, peer.port, peer.node_id))
            print()
            current_node = current_node.right

        index += 1


def simple_test():
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
    # display_table_content(table)


def left_leaf_test():
    bucket: KBucket = KBucket("100")
    left_leaf: LeftLeaf = LeftLeaf(host_key=0, bucket=bucket, bucket_prefix="100")

    # Test update function

    # Leaf should raise error if invalid prefix
    with pytest.raises(ValueError):
        left_leaf.update(NodeTuple("", 0, node_id=0))

    # Test update bucket
    left_leaf: LeftLeaf = LeftLeaf(host_key=0, bucket=bucket, bucket_prefix="100")
    node = NodeTuple("", 0, 9)
    left_leaf.update(node)
    assert (left_leaf.bucket.contains(node))



left_leaf_test()
