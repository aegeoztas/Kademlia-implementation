import asyncio
import os
from asyncio import StreamReader, StreamWriter

from LocalNode import LocalNode
from kademlia_service import KademliaService
from Constants import *
from handler import Handler, KademliaHandler, DHTHandler

# TODO Load from Windows INI configuration file

HOST_KEY_PEM = "123456789"

KADEMLIA_IP = "127.0.0.1"
DHT_API_IP = "127.0.0.1"

KADEMLIA_PORT = 8889
DHT_API_PORT = 8890



async def handle_connection(reader: StreamReader, writer: StreamWriter, handler: Handler):

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


async def start_kademlia_server(kademlia_handler: KademliaHandler):
    server = await asyncio.start_server(
        lambda reader, writer: handle_connection(reader, writer, kademlia_handler),
        KADEMLIA_IP,  # Address to listen on
        KADEMLIA_PORT  # Port to listen on
    )
    print(f"Kademlia Server started on IP: {KADEMLIA_IP} and port {KADEMLIA_PORT}...")
    async with server:
        await server.serve_forever()

async def start_dht_api_server(dht_handler: DHTHandler):
    server = await asyncio.start_server(
        lambda reader, writer: handle_connection(reader, writer, dht_handler),
        DHT_API_IP,  # Address to listen on
        DHT_API_PORT  # Port to listen on
    )
    print(f"DHT API Server started on IP: {DHT_API_IP} and port {KADEMLIA_PORT}...")
    async with server:
        await server.serve_forever()


async def main():

    # Creation of the local node that contains all the functionalities of a peer.
    local_node: LocalNode = LocalNode(KADEMLIA_IP, KADEMLIA_PORT, HOST_KEY_PEM)

    # Creation of the kademlia handler that handle requests from the kademlia network.
    kademlia_handler = KademliaHandler(local_node)

    # Creation of the dht handler that handle requests from other VoidIP modules
    dht_handler = DHTHandler(kademlia_handler)
    yield server_node

    await asyncio.gather(
        start_dht_server(dht_handler),
        start_kademlia_server(kademlia_handler)




    dht_node =  LocalNode( '127.0.0.1', DHT_PORT)
    kademlia_node = LocalNode( '127.0.0.1', KADEMLIA_PORT)
    kademlia_handler = KademliaHandler(kademlia_node)
    dht_handler = DHTHandler(kademlia_handler)


    await asyncio.gather(
        start_dht_server(dht_handler),
        start_kademlia_server(kademlia_handler)
    )


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



