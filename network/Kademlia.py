from dotenv import  load_dotenv
from Network import Connection
import os
"""
the kademlia library to implement the functions of kademlia protocol.
uses communication.py to communicate with others. 
"""

def PUT(Key, Value, connection=None ):
    """
This message is used to ask the DHT module that the given key-value pair should be stored.
The field TTL indiates the time in seconds this key-value pair should be stored in
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
size(16b\2B) + DHT PUT(16b\2B)
TLL (16b\2B)+ replication(8b\1B) +reserved(8b\1B)
key (256b\32B)
value (256b\32B)
    """
    message_type = os.getenv('DHT_PUT')
    TLL = 180
    replication = 2
    reserved = 0 # reserved for future use so just use 0


    data = TLL.to_bytes(2, byteorder='big')
    data += replication.to_bytes(1, byteorder='big')
    data += reserved.to_bytes(1, byteorder='big')
    data += Key.to_bytes(32, byteorder='big')
    data += Value.to_bytes((Value.bit_length() + 7)//8, byteorder='big')
    if connection:
        connection.send_message(message_type, data)
    else:
        load_dotenv()
        IP = os.getenv('IP')
        PORT = os.getenv('PORT')
        connection = Connection(IP, PORT)
        connection.connect()
        connection.send_message(message_type,data)
        connection.close()


    # reserved is just empty space

def GET(Key, connection=None ):
    """
    Sends a get message using key sends a get query to the tree, then im

    """
    message_type = os.getenv('DHT_GET')
    data = Key.to_bytes(32, byteorder='big')
    if connection:
        connection.send_message(message_type, data)
    else:
        load_dotenv()
        IP = os.getenv('IP')
        PORT = os.getenv('PORT')
        connection = Connection(IP, PORT)
        connection.connect()
        connection.send_message(message_type,data)
    # No imediate reply should be expected.
    # Should we create a thread for this? no that'd be stupid

    recieved_type, recieved_data = connection.receive_message()

    if recieved_type ==  os.getenv('DHT_SUCCESS'):
        key = recieved_data[:32]
        value = recieved_data[32:]
        return key,value
    elif recieved_type == os.getenv('DHT_FAILURE'):
        key = recieved_data[:32]
        return key, None
    else:
        print(f'something messed up recieved {recieved_type} instead of {message_type}')
        return None, None


def SUCCESS(Key, Value, connection=None ):
    """
    send a successful response containing key and found value
    """
    message_type = os.getenv('DHT_SUCCESS')

    data = Key.to_bytes(32, byteorder='big')
    data += Value.to_bytes((Value.bit_length() + 7) // 8, byteorder='big')
    if connection:
        connection.send_message(message_type, data)
    else:
        load_dotenv()
        IP = os.getenv('IP')
        PORT = os.getenv('PORT')
        connection = Connection(IP, PORT)
        connection.connect()
        connection.send_message(message_type, data)
        connection.close()

def FAILURE(Key, Value, connection=None ):
    """
    send a successful response containing key and found value
    """
    message_type = os.getenv('DHT_FAILURE')

    data = Key.to_bytes(32, byteorder='big')

    if connection:
        connection.send_message(message_type, data)
    else:
        load_dotenv()
        IP = os.getenv('IP')
        PORT = os.getenv('PORT')
        connection = Connection(IP, PORT)
        connection.connect()
        connection.send_message(message_type, data)
        connection.close()