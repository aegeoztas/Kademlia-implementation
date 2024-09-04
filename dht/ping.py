import secrets
import socket
import struct
from constants import *


def sync_ping_node(handler_ip: str, handler_port: int, local_node_id: int, remote_ip: str, remote_port: int):
    """
    This method is used to send a PING message in a synchronous manner.
    :param handler_ip: The IP of the host to ping.
    :param handler_port: The port of the host to ping.
    :param local_node_id:
    :param remote_ip:
    :param remote_port:
    :return:
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(TIME_OUT)
    try:
        # Establish connection with remote peer
        sock.connect((remote_ip, remote_port))

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
        node_id_field: bytes = local_node_id.to_bytes(32, byteorder='big')
        ip_handler_field: bytes = socket.inet_aton(handler_ip)
        port_handler_field: bytes = struct.pack(">H", handler_port)


        rpc_id: bytes = secrets.token_bytes(RPC_ID_FIELD_SIZE)

        # Create full message
        full_message: bytes = (size_field + message_type_field + node_id_field + ip_handler_field
                               + port_handler_field + rpc_id)

        # Send the full message to the server
        sock.sendall(full_message)

        # Receive response from the server


        response_size_bytes = sock.recv(SIZE_FIELD_SIZE)
        response_size: int = struct.unpack(">H", response_size_bytes)[0]

        response_body = sock.recv(response_size-SIZE_FIELD_SIZE)

        """
        Structure of PING_RESPONSE message
        +-----------------+----------------+---------------+---------------+
        |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
        +-----------------+----------------+---------------+---------------+
        |  Size           |  0             |  1            |  2            |
        +-----------------+----------------+---------------+---------------+
        |  Message type   |  2             |  3            |  2            |
        +-----------------+----------------+---------------+---------------+
        |  RPC ID         |  4             |  19           |  16           |
        +-----------------+----------------+---------------+---------------+
        """
        if len(response_body) < MESSAGE_TYPE_FIELD_SIZE + RPC_ID_FIELD_SIZE:
            # Ping response has invalid body
            return False

        message_type = int.from_bytes(response_body[:MESSAGE_TYPE_FIELD_SIZE], byteorder='big')
        rpc_id_resp: bytes = response_body[MESSAGE_TYPE_FIELD_SIZE:RPC_ID_FIELD_SIZE]
        if message_type == Message.PING_RESPONSE and rpc_id == rpc_id_resp:
            return True
        else:
            return False

    except socket.timeout:
        # In case of timeout we return false
        return False

    except Exception:
        # Error while sending or receiving message.
        return False