import asyncio
import os
import secrets
import struct
import sys
from asyncio import StreamReader, StreamWriter
from dotenv import load_dotenv
from MessageTypes import Message


load_dotenv()

# Global variable
SIZE_FIELD_SIZE = int(os.getenv("SIZE_FIELD_SIZE"))
MESSAGE_TYPE_FIELD_SIZE = int(os.getenv("MESSAGE_TYPE_FIELD_SIZE"))
RPC_ID_FIELD_SIZE = int(os.getenv("RPC_ID_FIELD_SIZE"))




async def send_message(message_type: int, payload: bytes, host: str, port: int):

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
        size_of_message: int = SIZE_FIELD_SIZE + MESSAGE_TYPE_FIELD_SIZE + len(
            payload)  # Total size including the size field

        size_field: bytes = struct.pack(">H", size_of_message)
        message_type_field: bytes = struct.pack(">H", message_type)

        # Create full message
        full_message: bytes = size_field + message_type_field + payload

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


async def send_ping(host: str, port: int):
    """
    This function is used to send a ping request and to process the response
    :param host: the recipient IP address
    :param port: the port of the recipient
    :return: True if it the recipient responded
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
    |  RPC ID         |  4             | 19            | 16            |
    +-----------------+----------------+---------------+---------------+
    """


    rpc_id : bytes= secrets.token_bytes(16)


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

    if message_type == Message.PING_RESPONSE and payload == rpc_id:
        print("Ping successful")
        return True


    else:
        print("Ping failed")
        return False




if __name__ == "__main__":
    # Example usage
    # message_type = 56 # Example message type
    # payload = b'Hello, Server!'  # Example payload
    #
    # asyncio.run(send_message(message_type, payload, '127.0.0.1', 8888))

    remote_ip = "127.0.0.1"
    remote_port = 8888
    asyncio.run(send_ping(remote_ip, remote_port))

