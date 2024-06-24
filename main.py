import random
import argparse
import asyncio
from socket import AF_INET
from kademlia.routing_table import RoutingTable
from kademlia.k_bucket import NodeTuple
from network.Messages import GET, PUT,SUCCESS,FAILURE
from network.Network import Connection


DHT_ADDR = "127.0.0.1"
DHT_PORT = 7401


DHT_PUT = 650
DHT_GET = 651
DHT_SUCCESS = 652
DHT_FAILURE = 653

async def handle_connection(reader, writer,kbucket,rtable):
    connection = Connection()
    connection.connect(reader, writer)
    try:
        while True:
            # Read the message header
            message_type, data= connection.recieve_message()


            if message_type == DHT_PUT:
                key = data[:32] # Read the key of the data
                value = data[32:] # Read rest of it
                # TODO Store Value using kademlia.

            elif message_type == DHT_GET:
                key = data[:32]  # Read the key of the data
                # TODO try to get the value of the get function.

                # assume you get some value
                value = "asfasdfasdfadsf"
                if value is not None:
                    await SUCCESS(key, value, connection)
                else:
                    # TODO if value is not here try to look up in kademlia tree.
                    await FAILURE(key, None, connection)

            else:
                print(f"Unknown message type: {message_type}")
                break
    except asyncio.IncompleteReadError:
        print("Client disconnected")
    finally:
        writer.close()
        await writer.wait_closed()

def handle_storage():
    """
    this function implements a kademlia tree like structure.

    creates internal and left right nodes.
    """

    # routing table requires an internal node

def main():

    # add cmd config
    # taken from the mockup for ease of use

    host = DHT_ADDR
    port = DHT_PORT

    # parse commandline arguments
    usage_string = ("Run a DHT module mockup with local storage.\n\n"
                    + "Multiple API clients can connect to this same instance.")
    cmd = argparse.ArgumentParser(description=usage_string)
    cmd.add_argument("-a", "--address",
                     help="Bind server to this address")
    cmd.add_argument("-p", "--port",
                     help="Bind server to this port")
    args = cmd.parse_args()

    if args.address is not None:
        host = args.address

    if args.port is not None:
        port = args.port

    # our node needs to have a k bucket
    # in dht put they have a 16 bit place
    # we are going to use first 8 as a dht id, should be enough
    local_node_id = random.getrandbits(0, 255)
    table: RoutingTable = RoutingTable(local_node_id)
    # routing table is only for knowing where to send messages and know which peers are closest to us in the abstract way




    # TODO implement storage lock
    loop = asyncio.get_event_loop()
    # create a lambda func that takes reader r, writer w, m(essage)handler
    # returns handle_client(r, w, mhandler)
    handler = lambda r, w, kbucket="kbucket",rtable="rtable": handle_connection(r, w, kbucket, rtable)

    server =  asyncio.start_server(handler, host=host, port=port,
                                    family=AF_INET,
                                    reuse_address=True,
                                    reuse_port=True )
    loop.create_task(server)

    print(f"[+] DHT team 17 listening on {host}:{port}")
    try:
        loop.run_forever()
    except KeyboardInterrupt as e:
        print("[i] Received SIGINT, shutting down...")
        loop.stop()


if __name__ == '__main__':
    main()
