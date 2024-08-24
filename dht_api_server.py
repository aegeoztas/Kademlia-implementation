import asyncio
import os
from asyncio import StreamReader, StreamWriter

from LocalNode import LocalNode
from dht_api_handler import DHT_APIHandler

from dotenv import load_dotenv

from kademlia_handler import KademliaHandler

load_dotenv()

# Global variable
SIZE_FIELD_SIZE = int(os.getenv("SIZE_FIELD_SIZE"))
MESSAGE_TYPE_FIELD_SIZE = int(os.getenv("MESSAGE_TYPE_FIELD_SIZE"))
# Environment variables
DHT_PORT = 8890
KADEMLIA_PORT =  8889


async def handle_connection(reader: StreamReader, writer: StreamWriter, handler):
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

async def start_dht_server(handler):
    server = await asyncio.start_server(
        lambda reader, writer: handle_connection(reader, writer, handler),
        '127.0.0.1',  # Address to listen on
        DHT_PORT  # Port to listen on
    )
    print(f"DHT Server started on port {DHT_PORT}...")
    async with server:
        await server.serve_forever()


async def start_kademlia_server(handler):
    server = await asyncio.start_server(
        lambda reader, writer: handle_connection(reader, writer, handler),
        '127.0.0.1',  # Address to listen on
        KADEMLIA_PORT  # Port to listen on
    )
    print(f"Kademlia Server started on port {KADEMLIA_PORT}...")
    async with server:
        await server.serve_forever()
async def main():
    dht_node =  LocalNode( '127.0.0.1', DHT_PORT)
    kademlia_node = LocalNode( '127.0.0.1', KADEMLIA_PORT)
    kademlia_handler = KademliaHandler(kademlia_node)
    dht_handler = DHT_APIHandler(dht_node, kademlia_handler)


    await asyncio.gather(
        start_dht_server(dht_handler),
        start_kademlia_server(kademlia_handler)
    )
if __name__ == "__main__":
    asyncio.run(main())

# Todo add timeout


