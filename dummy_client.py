import asyncio
import os
import struct
from asyncio import StreamReader, StreamWriter
from dotenv import load_dotenv

load_dotenv()

# Global variable
SIZE_FIELD_SIZE = int(os.getenv("SIZE_FIELD_SIZE"))
MESSAGE_TYPE_FIELD_SIZE = int(os.getenv("MESSAGE_TYPE_FIELD_SIZE"))


async def send_message(message_type: int, payload: bytes, host: str, port: int):

    # Declaration of reader and writer
    reader: StreamReader
    writer: StreamWriter

    try:
        # Establish connection to server
        reader, writer = await asyncio.open_connection(host, port)

        # Determine the size of the message and create the size field
        size_of_message: int = SIZE_FIELD_SIZE  + MESSAGE_TYPE_FIELD_SIZE + len(payload) # Total size including the size field

        size_field: bytes = struct.pack(">H", size_of_message)
        message_type_field: bytes = struct.pack(">H", message_type)


        # Create full message
        full_message: bytes = size_field + message_type_field + payload

        # Send the full message to the server
        writer.write(full_message)
        await writer.drain()  # Ensure the message is sent

        # # Await response from the server
        # response = await reader.read(100)  # Adjust size depending on expected response
        # print(f"Received response: {response.decode()}")

    except Exception as e:
        print(f"Error communicating with server: {e}")

    finally:
        writer.close()
        await writer.wait_closed()

if __name__ == "__main__":
    # Example usage
    message_type = 56 # Example message type (1 byte)
    payload = b'Hello, Server!'  # Example payload

    asyncio.run(send_message(message_type, payload, '127.0.0.1', 8888))
