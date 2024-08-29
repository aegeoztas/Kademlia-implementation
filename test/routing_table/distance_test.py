import random
import secrets
import sys
import os

# Add the project directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dht.xor_distance import key_distance


def generate_random_id() -> int:
    # Generate a random integer using secrets.token_bytes()
    random_bytes = secrets.token_bytes(20)  # 20 bytes = 160 bits
    random_int = int.from_bytes(random_bytes, 'big')

    return random_int


def id_distance_test():
    # Non-Euclidean metric
    # Property 1
    assert (key_distance(0, 0) == 0)
    # Property 2 symmetry
    a = random.randint(1, 5000)
    b = random.randint(1, 5000)
    assert (key_distance(a, b) == key_distance(b, a))

    # Property 3 triangle property
    c = random.randint(1, 5000)
    assert (key_distance(a, b) + key_distance(b, c) >= key_distance(c, b))

    #Choosed specific test
    x1 = "100"
    x2 = "101"
    assert (key_distance(int(x1, 2), int(x2, 2)) == 1)

    x3 = "111111111111111111111111"
    assert (key_distance(0, int(x3, 2)) == int(x3, 2))

    # random test
    x4 = generate_random_id()
    x5 = generate_random_id()

    assert (key_distance(x4, x5) == x4 ^ x5)


id_distance_test()
