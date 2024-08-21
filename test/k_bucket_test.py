import math
import random
from collections import deque

import pytest
from context import kademlia
from kademlia.k_bucket import *

from kademlia.dummy import *

def get_random_valid_node_tuple()->NodeTuple:
    ip_value = random.randint(0, 100)
    port = random.randint(0, 5000)
    id = random.randint(0, 5000)
    return NodeTuple(str(ip_value), port, id)


def node_tuple_constructor_test():
    # invalid parameters

    # negative port
    with pytest.raises(ValueError):
        a = NodeTuple("", -1, 0)

    #  port too big
    with pytest.raises(ValueError):
        a = NodeTuple("", 100000, 0)
    # negative node_id
    with pytest.raises(ValueError):
        a = NodeTuple("", 0, -1)
    #  node_id to big : test with key length 256
    with pytest.raises(ValueError):
        a = NodeTuple("", 0, int(math.pow(2, 257)))

    # test with random values
    a = random.randint(-5, 10000)
    b = random.randint(0, 20000)
    c = random.randint(0, 15)
    result = NodeTuple(str(a), b, c)
    assert (result.ip_address == str(a) and result.node_id == c and result.port == b)

    # edge cases
    port = 0
    node_id = 0
    result = NodeTuple("", port, node_id)
    assert (result.node_id == 0 and result.port == 0)
    port = 65535
    node_id = 2 ** 4 - 1
    result = NodeTuple("", port, node_id)
    assert (result.node_id == node_id and result.port == port)

def eq_node_tuple_test():
    # 1 : classic not equal
    a = get_random_valid_node_tuple()
    b = get_random_valid_node_tuple()
    a.port = 1
    b.port = 2
    assert(not (a == b))

    # 2 classic equal
    c = get_random_valid_node_tuple()
    d = get_random_valid_node_tuple()
    ip_value = random.randint(0, 100)
    port = random.randint(0, 5000)
    id = random.randint(0, 5000)

    c.ip_address = str(ip_value)
    c.port = port
    c.node_id = id
    d.ip_address = str(ip_value)
    d.port = port
    d.node_id = id
    assert (c == d)

def key_distance_to_test():
    a = get_random_valid_node_tuple()
    b = get_random_valid_node_tuple()
    assert(key_distance(a.node_id, b.node_id) == a.key_distance_to(b.node_id))

def binary_representation_test():
    # Contains no assert, just print
    a = get_random_valid_node_tuple()
    print(NodeTuple.node_id_binary_representation(a.node_id))

def has_prefix_test():
    # Chosen prefix
    prefix = "0000000000000000"
    id = 55
    assert(NodeTuple.has_prefix(id, prefix))
    prefix = "11111"
    id = int(math.pow(2, 256)) -1
    # rep = NodeTuple.node_id_binary_representation(id)
    assert(NodeTuple.has_prefix(id, prefix))

def print_node_tuple_test():
    a: NodeTuple = get_random_valid_node_tuple()
    print(a)


# Assert
eq_node_tuple_test()
node_tuple_constructor_test()
key_distance_to_test()
has_prefix_test()
# Printable
# binary_representation_test()
# print_node_tuple_test()


def k_bucket_constructor_test():
    # Test valid parameters
    a = KBucket("")
    assert (a.bucket_prefix == "")
    assert (a.size == 0)
    assert (len(a.bucket) == 0)


def update_bucket_parameters_test():
    b = KBucket("")

    # invalid parameters
    # negative port
    with pytest.raises(ValueError):
        b.update_bucket("", -1, 0)

    #  port to big
    with pytest.raises(ValueError):
        b.update_bucket("", 100000, 0)
    # negative id
    with pytest.raises(ValueError):
        b.update_bucket("", 0, -1)
    # to big id
    with pytest.raises(ValueError):
        b.update_bucket("", 0, 2 ** 161)

    # wrong prefix
    b = KBucket("1")
    with pytest.raises(ValueError):
        b.update_bucket("", 0, 0)
    b = KBucket("000")
    with pytest.raises(ValueError):
        b.update_bucket("", 0, 2 ** 160 - 1)

    # Valid arguments

    # right prefix and random other arguments
    b = KBucket("0000000000")
    port = random.randint(0, 65000)
    node_id = random.randint(0, 10000)
    b.update_bucket("", port, node_id)

    b = KBucket("11111111111111111111")
    b.update_bucket("", port, 2 ** 160 - 5)


def update_bucket_test_1():
    b = KBucket("")

    # Test size
    assert (b.size == 0)
    assert (len(b.bucket) == 0)

    # Test add node
    b.update_bucket("", 0, 2)
    assert (b.size == b.size == len(b.bucket) == 1)
    assert (not b.is_full())
    node = b.bucket.pop()
    assert (node.ip_address == "" and node.port == 0 and node.node_id == 2)

    # test fifo
    new_bucket = KBucket("")
    new_bucket.update_bucket("", 0, 2)
    new_bucket.update_bucket("", 0, 3)
    assert (new_bucket.bucket.pop().node_id == 2)


def is_full_test():
    # test full WORK ONLY FOR K = 4
    full_bucket = KBucket("")
    full_bucket.update_bucket("", 0, 3)
    full_bucket.update_bucket("", 0, 4)
    full_bucket.update_bucket("", 0, 5)
    assert (not full_bucket.is_full())
    full_bucket.update_bucket("random", 5, 4)
    assert (full_bucket.is_full())


def add_node_when_full_with_dummy_ping_test():
    # Test only work for K = 4

    bucket = KBucket("")

    bucket.update_bucket("first", 1, 0)
    bucket.update_bucket("second", 2, 1)
    bucket.update_bucket("third", 3, 2)
    bucket.update_bucket("forth", 4, 3)

    assert (bucket.is_full())

    bucket.update_bucket("fifth", 5, 4)

    if ping_node("", 0, 0):
        assert (bucket.bucket.popleft().ip_address == "first")
        assert (bucket.bucket.popleft().ip_address == "forth")
        assert (bucket.bucket.popleft().ip_address == "third")
        assert (bucket.bucket.popleft().ip_address == "second")

    else:
        assert (bucket.bucket.popleft().ip_address == "fifth")
        assert (bucket.bucket.popleft().ip_address == "forth")
        assert (bucket.bucket.popleft().ip_address == "third")
        assert (bucket.bucket.popleft().ip_address == "second")


def update_bucket_test_when_node_already_in_bucket():
    new_bucket = KBucket("")
    new_bucket.update_bucket("one", 1, 0)
    new_bucket.update_bucket("two", 2, 1)
    new_bucket.update_bucket("three", 3, 2)
    new_bucket.update_bucket("four", 4, 3)
    assert (new_bucket.size == 4 and new_bucket.is_full())
    new_bucket.update_bucket("three", 3, 2)
    assert (new_bucket.size == 4)
    assert (new_bucket.bucket.popleft().ip_address == "three")
    assert (new_bucket.bucket.popleft().ip_address == "four")
    assert (new_bucket.bucket.popleft().ip_address == "two")
    assert (new_bucket.bucket.popleft().ip_address == "one")


def contains_test():
    new_bucket = KBucket("")
    new_bucket.update_bucket("one", 1, 0)
    assert (new_bucket.contains("one", 1, 0))
    assert (not new_bucket.contains("", 1, 0))


def node_triple_binary_repr_test():
    node = NodeTuple("", 1, 5)

    # Assume a key length of 4 : change global variable KEY_LENGTH
    assert (NodeTuple.node_id_binary_representation(node.node_id) == "0101")


# node_tuple_constructor_test()
# k_bucket_constructor_test()
# update_bucket_parameters_test()
# update_bucket_test_1()
# is_full_test()
# add_node_when_full_with_dummy_ping_test()
# update_bucket_test_when_node_already_in_bucket()
# contains_test()
