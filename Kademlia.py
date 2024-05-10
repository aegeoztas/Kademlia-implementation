

"""
the kademlia librarz to implement the functions of kademlia protocol.
uses communication.py to communicate with others. 
"""

def PUT():
    """
This message is used to ask the DHT module that the given key-value pair should be stored.
The field TTL indicates the time in seconds this key-value pair should be stored in
the network before it is considered as expired. Note that this is just a hint. The peers may
have their own timeouts configured which may be shorter than the value in TTL. In those
cases the content could be expired beforehand.
The DHT does not make any guarantees about the content availability,
however it should exercise best effort to store it for that long.
Similarly, the replication field indicates how many times (by storing the content on
different peers, or under different keys, etc) this content should be replicated. This value
should also be treated as a hint.
The DHT may choose replicate more or less according to its parameters.
It is expected that the DHT module upon receiving this message does its best effort in
storing the given key-value pair. No confirmation is needed for the PUT operation. Request
of and storage of empty values is not allowed.

message itself contains
size(128b) + DHT PUT(128b)
TLL (128b)+ replication(64b) +reserved(64b)
key (256b)
value (256b)
    """
    TLL = 180
    replication = 2
    # reserved is just empty space

    pass
def GET():
    pass

