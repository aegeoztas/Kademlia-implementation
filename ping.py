import secrets

from k_bucket import NodeTuple
import socket
import struct
from constants import *


def sync_ping_node(local_node: NodeTuple, node_to_ping: NodeTuple):

    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    full_response = None

    try:
        # Establish connection with remote peer
        sock.connect((node_to_ping.ip_address, node_to_ping.port))

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
        |  IP handler     |  36            | 39            |  4            |
        +-----------------+----------------+---------------+---------------+
        |  Port handler   |  40            | 41            |  2            |
        +-----------------+----------------+---------------+---------------+
        |  RPC ID         |  42            |  15           |  16           |
        +-----------------+----------------+---------------+---------------+
        """


        # Determine the size of the message and create the size field
        size_of_message: int = (SIZE_FIELD_SIZE + MESSAGE_TYPE_FIELD_SIZE + KEY_SIZE + IP_FIELD_SIZE + PORT_FIELD_SIZE
                                + RPC_ID_FIELD_SIZE)  # Total size including the size field
        size_field: bytes = struct.pack(">H", size_of_message)
        message_type_field: bytes = struct.pack(">H", Message.PING)
        node_id_field: bytes = local_node.node_id.to_bytes(32, byteorder='big')
        ip_handler_field: bytes = socket.inet_aton(local_node.ip_address)
        port_handler_field: bytes = struct.pack(">H", local_node.port)


        rpc_id: bytes = secrets.token_bytes(RPC_ID_FIELD_SIZE)

        # Create full message
        full_message: bytes = (size_field + message_type_field + node_id_field + ip_handler_field
                               + port_handler_field + rpc_id)

        # Send the full message to the server
        sock.sendall(full_message)


        # Receive response from the server
        response_size_bytes = sock.recv(SIZE_FIELD_SIZE)
        response_size: int = struct.unpack(">H", response_size_bytes)[0]
        response = sock.recv(response_size)
        full_response = response_size_bytes + response

    except Exception as e:
        raise Exception(f"Error while sending or receiving message: {e}")

    finally:
        sock.close()
        return full_response


def dummy_ping_node(ip_address: str, port: int, node_id: int)-> bool:
    """
    The method serves as a dummy method for testing purpose
    The method should return true if the peer respond to the ping request and false if it does not respond.
    """
    success = True
    return success
