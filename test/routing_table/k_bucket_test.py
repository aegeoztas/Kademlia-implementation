import random
import pytest
import sys
import os

# Add the project directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dht.k_bucket import *

def get_random_valid_node_tuple()->NodeTuple:
    ip_value = random.randint(0, 100)
    port = random.randint(0, 5000)
    id = random.randint(0, 5000)
    return NodeTuple(str(ip_value), port, id)

##############################################################
##### NodeTuple
##############################################################

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

##############################################################
##### K_Bucket
##############################################################

def k_bucket_constructor_test():
    # Test valid parameters
    a = KBucket("")
    assert (a.bucket_prefix == "")
    assert (a.size == 0)
    assert (len(a.bucket) == 0)

def update_bucket_invalid_param():
    # invalid parameters
    with pytest.raises(ValueError):
        k_bucket: KBucket = KBucket("1")
        node_tuple: NodeTuple = get_random_valid_node_tuple()
        node_tuple.node_id = 0
        k_bucket.update_bucket(node_tuple)

def update_bucket_case_1_and_2():
    """
    Warning: K must be set to the value 2 in the .env file in order for this test to work.
    """

    # Test case 1 and case 2 [ Work only if K = 2 ! ]
    k_bucket : KBucket = KBucket("")
    first_node : NodeTuple = get_random_valid_node_tuple()
    second_node : NodeTuple = get_random_valid_node_tuple()
    k_bucket.update_bucket(first_node)
    k_bucket.update_bucket(second_node)
    k_bucket.update_bucket(first_node)
    assert (k_bucket.bucket.popleft() == first_node)
    assert (k_bucket.bucket.popleft() == second_node)

def update_bucket_case_3_ping_node_true():
    """
    Warning: K must be set to the value 2 in the .env file in order for this test to work.
            Dummy ping node must always return true in order for this test to pass
    """
    k_bucket : KBucket = KBucket("")
    first_node : NodeTuple = get_random_valid_node_tuple()
    second_node : NodeTuple = get_random_valid_node_tuple()
    third_node : NodeTuple = get_random_valid_node_tuple()
    k_bucket.update_bucket(first_node)
    k_bucket.update_bucket(second_node)


    k_bucket.update_bucket(third_node)

    assert (k_bucket.bucket.popleft() == first_node)
    assert (k_bucket.bucket.popleft() == second_node)
    assert (len(k_bucket.bucket) == 0)


def update_bucket_case_3_ping_node_false():
    """
    Warning: K must be set to the value 2 in the .env file in order for this test to work.
            Dummy ping node must always return false in order for this test to pass
    """
    k_bucket : KBucket = KBucket("")
    first_node : NodeTuple = get_random_valid_node_tuple()
    second_node : NodeTuple = get_random_valid_node_tuple()
    third_node : NodeTuple = get_random_valid_node_tuple()
    k_bucket.update_bucket(first_node)
    k_bucket.update_bucket(second_node)


    k_bucket.update_bucket(third_node)

    assert (k_bucket.bucket.popleft() == third_node)
    assert (k_bucket.bucket.popleft() == second_node)
    assert (len(k_bucket.bucket) == 0)


def is_full_test():
    # test full WORK ONLY FOR K = 2
    full_bucket = KBucket("")
    first_node : NodeTuple = get_random_valid_node_tuple()
    second_node : NodeTuple = get_random_valid_node_tuple()
    third_node : NodeTuple = get_random_valid_node_tuple()
    assert not full_bucket.is_full()
    full_bucket.update_bucket(first_node)
    assert not full_bucket.is_full()
    full_bucket.update_bucket(second_node)
    assert full_bucket.is_full()
    full_bucket.update_bucket(third_node)
    assert full_bucket.is_full()

def contains_test():
    new_bucket = KBucket("")
    first_node : NodeTuple = get_random_valid_node_tuple()
    assert not first_node in new_bucket
    new_bucket.update_bucket(first_node)
    assert first_node in new_bucket

def k_bucket_to_string_test():
    k_bucket: KBucket = KBucket("")
    first_node: NodeTuple = get_random_valid_node_tuple()
    second_node: NodeTuple = get_random_valid_node_tuple()
    third_node: NodeTuple = get_random_valid_node_tuple()
    k_bucket.update_bucket(first_node)
    k_bucket.update_bucket(second_node)
    k_bucket.update_bucket(third_node)
    print(k_bucket)


# Assert
eq_node_tuple_test()
node_tuple_constructor_test()
key_distance_to_test()
has_prefix_test()
k_bucket_constructor_test()
update_bucket_invalid_param()
update_bucket_case_1_and_2()
update_bucket_case_3_ping_node_true()
# update_bucket_case_3_ping_node_false() # Need to modify mock ping
is_full_test()
contains_test()

# Printable
# binary_representation_test()
# print_node_tuple_test()
# k_bucket_to_string_test()

