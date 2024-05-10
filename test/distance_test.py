import pytest
import random
import secrets
from context import kademlia

from kademlia import id_distance


def generate_random_id() -> int:
    # Generate a random integer using secrets.token_bytes()
    random_bytes = secrets.token_bytes(20)  # 20 bytes = 160 bits
    random_int = int.from_bytes(random_bytes, 'big')

    return random_int


def id_distance_test():
    # Non Euclidean metric
    # Property 1
    assert (id_distance(0, 0) == 0)
    # Property 2 symmetry
    a = random.randint(1, 5000)
    b = random.randint(1, 5000)
    assert (id_distance(a, b) == id_distance(b, a))

    # Property 3 triangle property
    c = random.randint(1, 5000)
    assert (id_distance(a, b) + id_distance(b, c) >= id_distance(c, b))

    #Choosed specific test
    x1 = "100"
    x2 = "101"
    assert (id_distance(int(x1, 2), int(x2, 2)) == 1)

    x3 = "111111111111111111111111"
    assert (id_distance(0, int(x3, 2)) == int(x3, 2))

    # random test
    x4 = generate_random_id()
    x5 = generate_random_id()

    assert (id_distance(x4, x5) == x4 ^ x5)


id_distance_test()
