# IDs of nodes and keys are of 160 bits
ID_SIZE = 160


def id_distance(id1: int, id2: int) -> int:
    return id1 ^ id2

