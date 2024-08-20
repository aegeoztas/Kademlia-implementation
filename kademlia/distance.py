
def key_distance(key1: int, key2: int) -> int:
    """
    Returns the value of the distance between two keys using the xor distance, as specified in the Kademlia paper.
    :param key1 : key or node_id of first object (int)
    :param key2: key or node_id of second object (int)
    :return: the xor distance expressed as an integer
    """
    return key1 ^ key2

