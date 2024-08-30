import asyncio
import argparse
from asyncio import StreamReader, StreamWriter

from local_node import LocalNode
from kademlia_service import KademliaService
from constants import *
from handler import Handler, KademliaHandler, DHTHandler

import config

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



async def main(known_peer_ip=None, known_peer_port=None, known_peer_id=None):

    # Get ip and ports from configuration file
    kademlia_handler_ip, kademlia_handler_port = config.get_address_from_conf("p2p_address")
    api_ip, api_port = config.get_address_from_conf("api_address")

    # Get the host_key from the configuration file
    try:
        host_key = config.get_public_key()
    except Exception as e:
        print(e)
        return



    # Creation of the local node that contains all the functionalities of a peer.
    local_node: LocalNode = LocalNode(kademlia_handler_ip, kademlia_handler_port, host_key)

    # Creation of the kademlia handler that handle requests from the kademlia network.
    kademlia_handler : KademliaHandler = KademliaHandler(local_node)

    # Creation the Kademlia service that is used to send requests in the kademlia network
    kademlia_service : KademliaService = KademliaService(local_node)

    # get known peer information:
    known_peer_ip, known_peer_port = config.get_address_from_conf("known_peer_address")
    if known_peer_ip and known_peer_port:
        await kademlia_service.send_join_network(known_peer_ip, known_peer_port)

    # Creation of the dht handler that handle requests from other VoidIP modules
    dht_handler : DHTHandler= DHTHandler(local_node, kademlia_service)



    await asyncio.gather(
        start_server(dht_handler, api_ip, api_port, handler_name="DHT API Server"),
        start_server(kademlia_handler, kademlia_handler_ip, kademlia_handler_port, handler_name="Kademlia Server"))

if __name__ == "__main__":

    # parser = argparse.ArgumentParser()
    # parser.add_argument("-ip", "--known_peer_ip", type=str, required=False, help="ip of one known peer inside the kademlia network")
    # parser.add_argument("-p", "--known_peer_port", type=int, required=False, help="port of one known peer inside the kademlia network")
    # parser.add_argument("-id", "--known_peer_id", type=int, required=False, help="ID of one known peer inside the kademlia network")
    # args = parser.parse_args()
    # asyncio.run(main(args.known_peer_ip, args.known_peer_port, args.known_peer_id))
    asyncio.run(main())




