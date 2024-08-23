import asyncio
import os
from asyncio import StreamReader, StreamWriter
from dummy_handler import DummyHandler

from dotenv import load_dotenv
load_dotenv()

# Global variable
SIZE_FIELD_SIZE = int(os.getenv("SIZE_FIELD_SIZE"))
MESSAGE_TYPE_FIELD_SIZE = int(os.getenv("MESSAGE_TYPE_FIELD_SIZE"))


async def handle_connection(reader: StreamReader, writer: StreamWriter, handler: DummyHandler):
    try:
        # Server read first two bytes to get size of message
        size_field = await reader.read(SIZE_FIELD_SIZE)
        size_of_message = int.from_bytes(size_field, byteorder='big')

        # Then server read rest of message
        buf = await reader.read(size_of_message - SIZE_FIELD_SIZE)

        full_message = size_field + buf

        # Handle the message request
        await handler.handle_message(full_message, reader, writer)
    except Exception as e:
        print(f"Error handling connection: {e}")
    finally:
        writer.close()
        await writer.wait_closed()

async def main():

    handler = DummyHandler()

    server = await asyncio.start_server(
        lambda reader, writer: handle_connection(reader, writer, handler),  # Pass the handler to the connection
        '127.0.0.1',  # Address to listen on
        8888  # Port to listen on
    )

    print("Server started...")

    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())

# Todo add timeout


