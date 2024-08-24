import asyncio
import os
import secrets
import struct
import socket
import sys
from asyncio import StreamReader, StreamWriter
from dotenv import load_dotenv
from MessageTypes import Message
from k_bucket import NodeTuple
from kademlia_handler import PORT_FIELD_SIZE

load_dotenv()

# Global variable
SIZE_FIELD_SIZE = int(os.getenv("SIZE_FIELD_SIZE"))
MESSAGE_TYPE_FIELD_SIZE = int(os.getenv("MESSAGE_TYPE_FIELD_SIZE"))
RPC_ID_FIELD_SIZE = int(os.getenv("RPC_ID_FIELD_SIZE"))
NUMBER_OF_NODES_FIELD_SIZE = int(os.getenv("NUMBER_OF_NODES_FIELD_SIZE"))
KEY_SIZE =int(os.getenv("KEY_SIZE"))
NB_OF_CLOSEST_PEERS = int(os.getenv("NB_OF_CLOSEST_PEERS"))
IP_FIELD_SIZE = int(os.getenv("IP_FIELD_SIZE"))



async def send_message(message_type: int, payload: bytes, host: str, port: int, node_id: int):

    # Declaration of reader and writer
    reader: StreamReader
    writer: StreamWriter
    full_response = None

    try:
        # Establish connection to server
        reader, writer = await asyncio.open_connection(host, port)

    except Exception as e:
        print(f"Connexion with server failed: {e}")
        return None

    try:
        # Determine the size of the message and create the size field
        size_of_message: int = SIZE_FIELD_SIZE + MESSAGE_TYPE_FIELD_SIZE + KEY_SIZE +  len(
            payload)  # Total size including the size field

        size_field: bytes = struct.pack(">H", size_of_message)
        message_type_field: bytes = struct.pack(">H", message_type)
        node_id_field: bytes =  node_id.to_bytes(32, byteorder='big')

        # Create full message
        full_message: bytes = size_field + message_type_field + node_id_field + payload

        # Send the full message to the server
        writer.write(full_message)
        await writer.drain()  # Ensure the message is sent

        # Await response from the server
        response_size_bytes = await reader.read(SIZE_FIELD_SIZE)
        response_size: int = struct.unpack(">H", response_size_bytes)[0]
        response = await reader.read(response_size)
        full_response = response_size_bytes + response

    except Exception as e:
        print(f"Error while sending or receiving message: {e}")


    finally:
        writer.close()
        await writer.wait_closed()
        return full_response


async def process_response(message: bytes):
    """
    This method extract the message type and the payload of a message
    :param message: the message payload (bytes)
    :return: the message type (int) and the payload (bytes)
    """
    if len(message) < SIZE_FIELD_SIZE + MESSAGE_TYPE_FIELD_SIZE:
        raise ValueError("Invalid response format, message too short")

    size = int(struct.unpack(">H", message[:SIZE_FIELD_SIZE])[0])
    message_type = int(struct.unpack(">H", message[SIZE_FIELD_SIZE:SIZE_FIELD_SIZE+MESSAGE_TYPE_FIELD_SIZE])[0])

    payload = message[SIZE_FIELD_SIZE+MESSAGE_TYPE_FIELD_SIZE:]

    return message_type, payload


async def send_ping(host: str, port: int, node_id: int):
    """
    This function is used to send a ping request and to process the response
    :param host: the recipient IP address
    :param port: the port of the recipient
    :param node_id: the node ID
    :return: True if the recipient responded
    """

    """
    Body of PING
    +-----------------+----------------+---------------+---------------+
    |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
    +-----------------+----------------+---------------+---------------+
    |  Size           |  0             |  1            |  2            |
    +-----------------+----------------+---------------+---------------+
    |  Message type   |  2             |  3            |  2            |
    +-----------------+----------------+---------------+---------------+
    |  Node ID        |  4             |  35           |  32           |
    +-----------------+----------------+---------------+---------------+
    |  RPC ID         |  36            | 51           | 16            |
    +-----------------+----------------+---------------+---------------+
    
    """

    rpc_id : bytes= secrets.token_bytes(16)


    response = await send_message(Message.PING, rpc_id, host, port, node_id)

    if not response:
        print("Ping failed")
        return False


    message_type: int=0
    payload : bytes=None

    try:
        message_type, payload = await process_response(response)

    except Exception as e:
        print(f"Error while processing response: {e}")

    if message_type == Message.PING_RESPONSE and payload == rpc_id:
        print("Ping successful")
        return True

    else:
        print("Ping failed")
        return False

async def send_find_node(host: str, port: int, node_id: int, key: int):
    """
    This function is used to send a find request and to process the response
    :param host: the recipient IP address
    :param port: the port of the recipient
    :param node_id: the node ID
    :return: True if the response was valid.
    """

    """
    Structure of request 
    +-----------------+----------------+---------------+---------------+
    |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
    +-----------------+----------------+---------------+---------------+
    |  Size           |  0             |  1            |  2            |
    +-----------------+----------------+---------------+---------------+
    |  Message type   |  2             |  3            |  2            |
    +-----------------+----------------+---------------+---------------+
    |  RPC ID         |  4             | 19            | 16            |
    +-----------------+----------------+---------------+---------------+
    |  key            |  20            | 48            | 51            |
    +-----------------+----------------+---------------+---------------+
    """

    rpc_id: bytes = secrets.token_bytes(16)

    content = rpc_id + int.to_bytes(key, 32, byteorder='big')

    response = await send_message(Message.FIND_NODE, content, host, port, node_id)

    if not response:
        print("Find node failed")
        return False

    message_type: int = 0
    payload: bytes = None

    try:
        message_type, payload = await process_response(response)

    except Exception as e:
        print(f"Error while processing response: {e}")

    """
    Structure of FIND_NODE_RESP message
    +-----------------+----------------+---------------+---------------+
    |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
    +-----------------+----------------+---------------+---------------+
    |  Size           |  0             |  1            |  2            |
    +-----------------+----------------+---------------+---------------+
    |  Message type   |  2             |  3            |  2            |
    +-----------------+----------------+---------------+---------------+
    |  RPC ID         |  4             |  19           |  16           |
    +-----------------+----------------+---------------+---------------+
    | nb_node_found   |  20            |  21           |  2            |
    +-----------------+----------------+---------------+---------------+
    | IP 1            |  22             |  -           |  4            |
    +-----------------+----------------+---------------+---------------+
    | port 1          |  -             |  -            |  2            |
    +-----------------+----------------+---------------+---------------+
    | node_id 1       |  -             |  -            |  32           |
    +-----------------+----------------+---------------+---------------+
    ...
    +-----------------+----------------+---------------+---------------+
    | IP n            |  -             |  -            |  4            |
    +-----------------+----------------+---------------+---------------+
    | port n          |  -             |  -            |  2            |
    +-----------------+----------------+---------------+---------------+
    | node_id n       |  -             |  -            |  32           |
    +-----------------+----------------+---------------+---------------+

    """

    if message_type == Message.FIND_NODE_RESP and payload[:RPC_ID_FIELD_SIZE] == rpc_id:
        index = RPC_ID_FIELD_SIZE
        nb_node_found = int.from_bytes(payload[index:index+NUMBER_OF_NODES_FIELD_SIZE], byteorder='big')
        index+=NUMBER_OF_NODES_FIELD_SIZE
        list_of_nodes :list[NodeTuple] = []
        for i in range(nb_node_found):
            ip = socket.inet_ntoa(payload[index:index+IP_FIELD_SIZE])
            index += IP_FIELD_SIZE
            port = int.from_bytes(payload[index:index+PORT_FIELD_SIZE], byteorder='big')
            index += PORT_FIELD_SIZE
            node_id = int.from_bytes(payload[index:index+KEY_SIZE], byteorder='big')
            index += KEY_SIZE
            list_of_nodes.append(NodeTuple(ip, port, node_id))

        print("Node contained:" )
        for node in list_of_nodes:
            print(node)


    else:
        print("Find node failed")
        return False


if __name__ == "__main__":
    # Example usage
    # message_type = 56 # Example message type
    # payload = b'Hello, Server!'  # Example payload
    #
    # asyncio.run(send_message(message_type, payload, '127.0.0.1', 8888))

    remote_ip = "127.0.0.1"
    remote_port = 8888
    asyncio.run(send_ping(remote_ip, remote_port, 55))

    asyncio.run(send_find_node(remote_ip, remote_port, 55, 0))



