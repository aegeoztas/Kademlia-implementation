import asyncio
import struct
import random
import subprocess
from asyncio import StreamReader, StreamWriter
import os
import time

import requests
import configparser
from cryptography.hazmat.primitives.asymmetric import rsa


"""
this test is for testing p2p interface of the dht implementation
"""
config = configparser.ConfigParser()

# Read the config.ini file
config.read('config.ini')
# Global variable
SIZE_FIELD_SIZE =2
MESSAGE_TYPE_FIELD_SIZE =2
"""
this is not working. 

"""


async def send_message(message_type: int, payload: bytes, host: str, port: int):

    # Declaration of reader and writer
    reader: StreamReader
    writer: StreamWriter
    full_response = None
    reader, writer = await asyncio.open_connection(host, port)
    try:
        # Establish connection to server


        # Determine the size of the message and create the size field
        size_of_message: int = SIZE_FIELD_SIZE  + MESSAGE_TYPE_FIELD_SIZE + len(payload) # Total size including the size field

        size_field: bytes = struct.pack(">H", size_of_message)
        message_type_field: bytes = struct.pack(">H", message_type)


        # Create full message
        full_message: bytes = size_field + message_type_field + payload

        # Send the full message to the server
        writer.write(full_message)
        await writer.drain()  # Ensure the message is sent

        # Await response from the server
        response_size_bytes = await reader.read(SIZE_FIELD_SIZE)
        response_size: int= struct.unpack(">H", response_size_bytes)[0]
        response = await reader.read(response_size)
        full_response = response_size_bytes + response



    except Exception as e:
        print(f"Error communicating with server: {e}")

    finally:
        writer.close()
        await writer.wait_closed()
        return full_response



async def test_put():
    api_host = "127.0.0.1"
    api_port = 8889
    message_type = 650  #  dht put
    TTL_FIELD_SIZE = 2
    REPLICATION_FIELD_SIZE = 1
    RESERVED_FIELD_SIZE = 1
    ttl = int.to_bytes(100, TTL_FIELD_SIZE, byteorder='big')
    replication = int.to_bytes(2, REPLICATION_FIELD_SIZE, byteorder='big')
    reserved = int.to_bytes(0, RESERVED_FIELD_SIZE, byteorder='big')
    key = int.to_bytes(12345, 32, byteorder='big')
    value = b"12345"
    payload = ttl + replication + reserved + key + value

    result =  await send_message(message_type=message_type, payload=payload, host=api_host, port=api_port)
    print(result)


if __name__ == "__main__":
    # Example usage
    # message_type = 56 # Example message type
    # payload = b'Hello, Server!'  # Example payload
    #
    # asyncio.run(send_message(message_type, payload, '127.0.0.1', 8888))

    remote_ip = "127.0.0.1"
    remote_port = 8888
    asyncio.run(tput())
