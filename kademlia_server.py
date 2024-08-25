import asyncio
import os
from asyncio import StreamReader, StreamWriter
from dotenv import load_dotenv

from LocalNode import LocalNode
from kademlia_handler import KademliaHandler
from kademlia_service import KademliaService

load_dotenv()

# Global variable
SIZE_FIELD_SIZE = int(os.getenv("SIZE_FIELD_SIZE"))
MESSAGE_TYPE_FIELD_SIZE = int(os.getenv("MESSAGE_TYPE_FIELD_SIZE"))

# TODO Load from Windows INI configuration file
IP = "127.0.0.1"
PORT = 8888
HOST_KEY_PEM = "123456789"


async def handle_connection(reader: StreamReader, writer: StreamWriter, handler: KademliaHandler):

    try:
        # Server read first two bytes to get size of message
        size_field = await reader.read(SIZE_FIELD_SIZE)
        size_of_message = int.from_bytes(size_field, byteorder='big')

        # Then server read rest of message
        buf = await reader.read(size_of_message - SIZE_FIELD_SIZE)

        full_message = size_field + buf

        # Handle the message request
        await handler.handle_request(full_message, reader, writer)
    except Exception as e:
        print(f"Error handling connection a: {e}")
    finally:
        writer.close()
        await writer.wait_closed()

async def main():

    local_node: LocalNode = LocalNode(IP, PORT, HOST_KEY_PEM)

    kademlia_handler : KademliaHandler= KademliaHandler(local_node)

    kademlia_service : KademliaService = KademliaService(local_node)

    server = await asyncio.start_server(
        lambda reader, writer: handle_connection(reader, writer, kademlia_handler),  # Pass the handler to the connection
        IP,  # Address to listen on
        PORT  # Port to listen on
    )

    print("Kademlia DHT server started...")

    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())



