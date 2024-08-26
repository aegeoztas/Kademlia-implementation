import asyncio
import os
from asyncio import StreamReader, StreamWriter

from LocalNode import LocalNode
from kademlia_service import KademliaService
from constants import *
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

async def start_server(handler: Handler, ip: str, port: int, handler_name: str):
    server = await asyncio.start_server(
        lambda reader, writer: handle_connection(reader, writer, handler),
        ip,  # Address to listen on
        port  # Port to listen on
    )
    print(f"{handler_name} started on IP: {ip} and port {port}...")
    async with server:
        await server.serve_forever()



async def main():

    # Creation of the local node that contains all the functionalities of a peer.
    local_node: LocalNode = LocalNode(KADEMLIA_IP, KADEMLIA_PORT, HOST_KEY_PEM)

    # Creation of the kademlia handler that handle requests from the kademlia network.
    kademlia_handler : KademliaHandler = KademliaHandler(local_node)

    # Creation the Kademlia service that is used to send requests in the kademlia network
    kademlia_service : KademliaService = KademliaService(local_node)

    # Creation of the dht handler that handle requests from other VoidIP modules
    dht_handler : DHTHandler= DHTHandler(local_node, kademlia_service)



    await asyncio.gather(
        start_server(dht_handler, DHT_API_IP, DHT_API_PORT, handler_name="DHT API Server"),
        start_server(kademlia_handler, KADEMLIA_IP, KADEMLIA_PORT, handler_name="Kademlia Server"))





if __name__ == "__main__":
    asyncio.run(main())



