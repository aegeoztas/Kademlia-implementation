import asyncio

import secrets
import struct
import socket

from asyncio import StreamReader, StreamWriter

from Constants import Message
from LocalNode import LocalNode
from k_bucket import NodeTuple

from Constants import *

async def send_message(message_type: int, payload: bytes, host: str, port: int,
                       no_response_expected: bool=False):

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

        """
        Message Format
        +-----------------+----------------+---------------+---------------+
        |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
        +-----------------+----------------+---------------+---------------+
        |  Size           |  0             |  1            |  2            |
        +-----------------+----------------+---------------+---------------+
        |  Message type   |  2             |  3            |  2            |
        +-----------------+----------------+---------------+---------------+
        |  Node ID        |  4             |  35           |  32           |
        +-----------------+----------------+---------------+---------------+
        |  IP handler     |  36            | 39            | 4             |
        +-----------------+----------------+---------------+---------------+
        |  Port handler   |  40            | 41            | 2             |
        +-----------------+----------------+---------------+---------------+
        |  Body           |  42            | end           | -             |
        +-----------------+----------------+---------------+---------------+
        """

        local_node: LocalNode = LocalNode("8.8.8.8", 88, "8888888")


        # Determine the size of the message and create the size field
        size_of_message: int = (SIZE_FIELD_SIZE + MESSAGE_TYPE_FIELD_SIZE + KEY_SIZE + IP_FIELD_SIZE + PORT_FIELD_SIZE
                                + len(payload))  # Total size including the size field

        size_field: bytes = struct.pack(">H", size_of_message)
        message_type_field: bytes = struct.pack(">H", message_type)
        node_id_field: bytes = local_node.node_id.to_bytes(32, byteorder='big')
        ip_handler_field: bytes = socket.inet_aton(local_node.handler_ip)
        port_handler_field: bytes = struct.pack(">H", local_node.handler_port)


        # Create full message
        full_message: bytes = (size_field + message_type_field + node_id_field + ip_handler_field
                               + port_handler_field + payload)

        # Send the full message to the server
        writer.write(full_message)
        await writer.drain()  # Ensure the message is sent


        if no_response_expected:
            return "Message sent"

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


async def send_ping(host: str, port: int):
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
    |  RPC ID         |  0             | 15            | 16            |
    +-----------------+----------------+---------------+---------------+
    """

    rpc_id : bytes= secrets.token_bytes(RPC_ID_FIELD_SIZE)


    response = await send_message(Message.PING, rpc_id, host, port)

    if not response:
        print("Ping failed")
        return False


    message_type: int=0
    payload : bytes=None

    try:
        message_type, payload = await process_response(response)

    except Exception as e:
        print(f"Error while processing response: {e}")

    """
    Structure of body of PING_RESPONSE
    +-----------------+----------------+---------------+---------------+
    |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
    +-----------------+----------------+---------------+---------------+
    |  RPC ID         |  0             | 15            | 16            |
    +-----------------+----------------+---------------+---------------+
    """
    if message_type == Message.PING_RESPONSE and payload == rpc_id:
        print("Ping successful")
        return True

    else:
        print("Ping failed")
        return False

async def send_store(host: str, port: int, key: int, ttl: int,  value: bytes)->bool:
    """
    This function is used to send a store request
    :param host: the recipient IP address
    :param port: the port of the recipient
    :param key: The key associated with the value.
    :param ttl: The time-to-live of the value.
    :param value: The value to be stored.
    :return: True if the operation was successful, False otherwise
    """
    """
    Body of STORE request 
    +-----------------+----------------+---------------+---------------+
    |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
    +-----------------+----------------+---------------+---------------+
    |  RPC ID         |  0             | 15            | 16            |
    +-----------------+----------------+---------------+---------------+
    |  key            |  20            | 51            | 32            |
    +-----------------+----------------+---------------+---------------+
    |  TTL            |  52            | 53            |  2            |
    +-----------------+----------------+---------------+---------------+
    |  value          |  54            | end           |   variable    |
    +-----------------+----------------+---------------+---------------+
    """

    # Creation of the content of the request
    rpc_id: bytes = secrets.token_bytes(RPC_ID_FIELD_SIZE)

    content : bytes = rpc_id
    content += int.to_bytes(key,32,  byteorder='big')
    content += struct.pack(">H", ttl)
    content += value

    if await send_message(Message.STORE, content, host, port, True) == "Message sent":
        return True
    else:
        return False

async def handle_find_node_resp(message_type: int, payload: bytes, rpc_id: bytes)-> bool:
    """
    This function is used to handle a find_node_resp
    :param message_type: the message type, should be FIND_NODE_RESP
    :param payload: the payload of the message
    :param rpc_id: The rpc_id of the request
    :return: true if the operation was successful, false otherwise
    """

    """
    Structure of body of FIND_NODE_RESP message
    +-----------------+----------------+---------------+---------------+
    |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
    +-----------------+----------------+---------------+---------------+
    |  RPC ID         |  0             |  15           |  16           |
    +-----------------+----------------+---------------+---------------+
    | nb_node_found   |  16            |  17           |  2            |
    +-----------------+----------------+---------------+---------------+
    | IP 1            |  18            |  -            |  4            |
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
        nb_node_found = int.from_bytes(payload[index:index + NUMBER_OF_NODES_FIELD_SIZE], byteorder='big')
        index += NUMBER_OF_NODES_FIELD_SIZE
        list_of_nodes: list[NodeTuple] = []
        for i in range(nb_node_found):
            ip = socket.inet_ntoa(payload[index:index + IP_FIELD_SIZE])
            index += IP_FIELD_SIZE
            port = int.from_bytes(payload[index:index + PORT_FIELD_SIZE], byteorder='big')
            index += PORT_FIELD_SIZE
            node_id = int.from_bytes(payload[index:index + KEY_SIZE], byteorder='big')
            index += KEY_SIZE
            list_of_nodes.append(NodeTuple(ip, port, node_id))

        print("Node contained:")
        for node in list_of_nodes:
            print(node)

        return True

    return False

async def send_find_node(host: str, port: int, key: int):
    """
    This function is used to send a find request and to process the response
    :param host: the recipient IP address
    :param port: the port of the recipient
    :param key: the key to find the closest nodes to.
    :return: True if the response was valid.
    """

    """
    Body of FIND_NODE request 
    +-----------------+----------------+---------------+---------------+
    |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
    +-----------------+----------------+---------------+---------------+
    |  RPC ID         |  0             | 15            | 16            |
    +-----------------+----------------+---------------+---------------+
    |  key            |  16            | 46            | 32            |
    +-----------------+----------------+---------------+---------------+
    """

    rpc_id: bytes = secrets.token_bytes(RPC_ID_FIELD_SIZE)

    content = rpc_id + int.to_bytes(key, 32, byteorder='big')

    response = await send_message(Message.FIND_NODE, content, host, port)

    if not response:
        print("Find node failed")
        return False

    message_type: int = 0
    payload: bytes = None

    try:
        message_type, payload = await process_response(response)

    except Exception as e:
        print(f"Error while processing response: {e}")

    if await handle_find_node_resp(message_type, payload, rpc_id):
        print("Find node successful")
    else:
        print("Find node failed")



async def send_find_value(host: str, port: int, key: int)->bool:
    """
    This function is used to send a find value request
    :param host: the recipient IP address
    :param port: the port of the recipient
    :param key: The key associated with the value.
    :return: True if the operation was successful, False otherwise
    """

    """
    Body of FIND_VALUE request
    +-----------------+----------------+---------------+---------------+
    |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
    +-----------------+----------------+---------------+---------------+
    |  RPC ID         |  0             | 16            | 16            |
    +-----------------+----------------+---------------+---------------+
    |  key            |  17            | 48            |  32           |
    +-----------------+----------------+---------------+---------------+
    """

    # Creation of the content of the request
    rpc_id: bytes = secrets.token_bytes(RPC_ID_FIELD_SIZE)

    content: bytes = rpc_id
    content += int.to_bytes(key, 32, byteorder='big')

    response: bytes = await send_message(Message.FIND_VALUE, content, host, port)

    if not response:
        print("FIND_VALUE request failed")
        return False

    message_type: int = 0
    payload: bytes = None

    try:
        message_type, payload = await process_response(response)

    except Exception as e:
        print(f"Error while processing response: {e}")

    """
    Body FIND_VALUE_RESP message
    +-----------------+----------------+---------------+---------------+
    |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
    +-----------------+----------------+---------------+---------------+
    |  RPC ID         |  0             |  15           |  16           |
    +-----------------+----------------+---------------+---------------+
    |  value          |  16            |  -            |  -            |
    +-----------------+----------------+---------------+---------------+
    """

    if message_type == Message.FIND_VALUE_RESP:
        if rpc_id == payload[:RPC_ID_FIELD_SIZE]:
            print("Find value successful")
            print(f"Value: {payload[RPC_ID_FIELD_SIZE:]}")
            return True
        else:
            print("Find value request failed")
            return False

    if message_type == Message.FIND_NODE_RESP:
        status : bool = await handle_find_node_resp(message_type, payload, rpc_id)
        if status:
            print("Find value request resulted in list of closest nodes")
            return True
        else:
            print("Find value request failed")
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
    asyncio.run(send_store(remote_ip, remote_port, 55, 658432, 400, b"Hello World"))
    asyncio.run(send_find_value(remote_ip, remote_port, 55, 658432))




