from collections import deque

import pytest
from context import kademlia
from kademlia.k_bucket import KBucket, NodeTriple
import random
from kademlia.dummy import *


def k_bucket_constructor_test():
    # test invalid parameters

    # k negative
    with pytest.raises(ValueError):
        a = KBucket("", -1)

    # Test valid parameters
    a = KBucket("", 0)
    x1 = ""
    x2 = random.randint(0, 100000)
    c = KBucket(x1, x2)
    assert (x1 == c.bucket_id and x2 == c.k)
    assert (c.size == 0)
    assert (len(c.bucket) == 0)


def node_triple_constructor_test():
    # invalid parameters
    # negative port
    with pytest.raises(ValueError):
        a = NodeTriple("", -1, 0)
    # negative node_id
    with pytest.raises(ValueError):
        a = NodeTriple("", 0, -1)

    # test with random values
    a = random.randint(-5, 10000)
    b = random.randint(0, 1000000)
    c = random.randint(0, 100000)
    result = NodeTriple(str(a), b, c)
    assert (result.ip_address == str(a) and result.node_id == c and result.port == b)


def add_node_parameters_test():
    empty = KBucket(0, 5)
    # invalid parameters

    # Test not relevant anymore due to changes
    # in the implementation
    # negative port
    # with pytest.raises(ValueError):
    #     empty.add_node("", -1, 0)
    # # negative id
    # with pytest.raises(ValueError):
    #     empty.add_node("", 0, -1)

    # random parameters
    a, b, c = random.sample(range(0, 10000), 3)
    empty.add_node(str(a), b, c)


def add_node_test():
    empty = KBucket(0, 5)

    # size
    assert (empty.size == 0)
    assert (not empty.is_full())
    assert (len(empty.bucket) == 0)

    # test add_node
    empty.add_node("", 0, 2)
    assert (empty.size == empty.size == len(empty.bucket) == 1)
    assert (not empty.is_full())
    node = empty.bucket.pop()
    assert (node.ip_address == "" and node.port == 0 and node.node_id == 2)

    # test fifo
    new_bucket = KBucket(0, 5)
    new_bucket.add_node("", 0, 2)
    new_bucket.add_node("", 0, 3)
    assert (new_bucket.bucket.pop().node_id == 2)

    # test full
    full_bucket = KBucket(0, 3)
    full_bucket.add_node("", 0, 3)
    full_bucket.add_node("", 0, 4)
    assert (not full_bucket.is_full())
    full_bucket.add_node("random", 5, 4)
    assert (full_bucket.is_full())


def add_node_when_full_with_dummy_ping_test():
    bucket = KBucket(0, 2)

    bucket.add_node("first", 1, 0)
    bucket.add_node("second", 2, 1)
    assert (bucket.is_full())

    bucket.add_node("third", 3, 3)

    if ping_node("", 0, 0):
        assert (bucket.bucket.popleft().ip_address == "first")
    else:
        assert (bucket.bucket.popleft().ip_address == "third")
    assert (bucket.bucket.pop().ip_address == "second")


def update_bucket_parameters_test():
    empty = KBucket(0, 5)
    # invalid parameters

    #negative port
    with pytest.raises(ValueError):
        empty.update_bucket("", -1, 0)
    # negative id
    with pytest.raises(ValueError):
        empty.update_bucket("", 0, -1)

    # random parameters
    a, b, c = random.sample(range(0, 10000), 3)
    empty.update_bucket(str(a), b, c)


def update_bucket_test():
    new_bucket = KBucket(0, 5)
    new_bucket.update_bucket("one", 1, 0)
    new_bucket.update_bucket("two", 2, 1)
    new_bucket.update_bucket("three", 3, 2)
    new_bucket.update_bucket("four", 4, 3)
    assert (new_bucket.size == 4)
    new_bucket.update_bucket("three", 3, 2)
    assert (new_bucket.size == 4)
    assert (new_bucket.bucket.popleft().ip_address == "three")
    assert (new_bucket.bucket.popleft().ip_address == "four")
    assert (new_bucket.bucket.popleft().ip_address == "two")
    assert (new_bucket.bucket.popleft().ip_address == "one")


def node_triple_binary_repr_test():
    node = NodeTriple("", 1, 5)

    # Assume a key length of 4 : change global variable KEY_LENGTH
    assert (NodeTriple.node_id_binary_representation(node.node_id) == "0101")


# k_bucket_constructor_test()
# node_triple_constructor_test()
# add_node_parameters_test()
# add_node_test()
# add_node_when_full_with_dummy_ping_test()
# update_bucket_parameters_test()
# update_bucket_test()
node_triple_binary_repr_test()
