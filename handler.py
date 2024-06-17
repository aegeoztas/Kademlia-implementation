import random
import argparse
import asyncio
from socket import AF_INET
from LocalNode import LocalNode
from kademlia import NodeTuple
from network.messages import *
from util import *
from network.Kademlia import GET, PUT, SUCCESS, FAILURE
from network.Network import Connection

DHT_ADDR = "127.0.0.1"
DHT_PORT = 7401

SIZE_FIELD_SIZE = 2
MESSAGE_TYPE_FIELD_SIZE = 2
KEY_FIELD_SIZE = 256 / 8
IP_FIELD_SIZE = 32 / 8
PORT_FIELD_SIZE = 16 / 8

NB_OF_CLOSEST_PEERS = 4


class Handler:

    def __init__(self, local_node: LocalNode):
        self.local_node: LocalNode = local_node

    async def handle_message(self, buf, reader, writer):
        """
        This function handles incoming requests according to their content.
        """
        return_status = False
        header = buf[:4]
        body = buf[4:]

        # Extracting the message type
        message_type = struct.unpack(">HH", header)[1]

        try:
            match message_type:
                case DHT_PING.value:
                    return_status = await self.handle_ping(reader, writer)
                case DHT_PUT.value:
                    return_status = await handle_put()
                case DHT_GET.value:
                    key = int.from_bytes(struct.unpack("B" * KEY_FIELD_SIZE, body[0: KEY_FIELD_SIZE - 1]))
                    return_status = await self.handle_get_request(reader, writer, key)
                case DHT_FIND_NODE.value:
                    key = int.from_bytes(struct.unpack("B" * KEY_FIELD_SIZE, body[0: KEY_FIELD_SIZE - 1]),
                                         byteorder="big")
                    return_status = await self.handle_find_nodes_request(reader, writer, key)
                case DHT_STORE.value:
                    ttl = int(struct.unpack(">H", body[0:1]))
                    replication = int(struct.unpack(">B", body[2]))
                    key = int.from_bytes(struct.unpack("B" * KEY_FIELD_SIZE, body[4: 4 + KEY_FIELD_SIZE - 1]),
                                         byteorder="big")
                    value_field_size = len(body) - KEY_FIELD_SIZE - 4
                    value = struct.unpack("B" * value_field_size, body[4 + KEY_FIELD_SIZE:])
                    return_status = await self.handle_store_request(ttl, key, value)
                case _:
                    await bad_packet(reader, writer,
                                     f"Unknown message type {message_type} received",
                                     header)
        except Exception as e:
            await bad_packet(reader, writer, f"Wrongly formatted message", buf)
        return return_status

    async def handle_ping(self, reader, writer):
        """
        This function handles a ping message. It will just send a pong response.
        :param reader: The reader of the socket.
        :param writer: The writer of the socket.
        :return: True if the operation was successful.
        """
        # Get the address of the remote peer
        remote_address, remote_port = writer.get_extra_info("socket").getpeername()
        # Define the ping response message
        message_size = int(SIZE_FIELD_SIZE + MESSAGE_TYPE_FIELD_SIZE)
        response = struct.pack(">HH", message_size, DHT_PING_RESP)
        # Send the response
        try:
            writer.write(response)
            await writer.drain()
        except Exception as e:
            print(f"[-] Failed to send PING_RESPONSE {e}")
            await bad_packet(reader, writer)
            return False

        print(f"[+] {remote_address}:{remote_port} <<< PING_RESPONSE")

        return True

    async def handle_store_request(self, ttl: int, key: int, value: bytes):
        """
        This function handles a store message. If this function is called, this node has been designated to store a value.
        It must then store the value in its storage.
        :param reader: The reader of the socket.
        :param writer: The writer of the socket.
        :param ttl: The time to live of the value to be stored.
        :param key: The 256 bit key associated to the value.
        :param value: The value to be stored.
        :return: True if the operation was successful.
        """
        self.local_node.local_hash_table.put(key, value, ttl)
        return True

    async def handle_get_request(self, reader, writer, key: int):
        """
        This method handles a get message. It the local node contains the data,
        it will simply return it. If not, it will try to get from the network.
        :param reader: The reader of the socket.
        :param writer: The writer of the socket.
        :param key: The key associated to the data.
        :return: True if the operation was successful.
        """
        # Get the address of the remote peer
        remote_address, remote_port = writer.get_extra_info("socket").getpeername()

        # Check if the value is in the local storage
        value = self.local_node.local_hash_table.get(key)
        if value is not None:
            # return value to the requester
            # Define the DHT Success message
            message_size = int(SIZE_FIELD_SIZE + MESSAGE_TYPE_FIELD_SIZE
                               + KEY_FIELD_SIZE + len(value))
            response = struct.pack(">HH", message_size,
                                   DHT_SUCCESS)
            response += struct.pack("B" * KEY_FIELD_SIZE, key)
            response += value
            # Send response
            try:
                writer.write(response)
                await writer.drain()
            except Exception as e:
                print(f"[-] Failed to send DHT_SUCCESS {e}")
                await bad_packet(reader, writer, data=response)
                return False

            print(f"[+] {remote_address}:{remote_port} <<< DHT_SUCCESS")
            return True

        else:
            # Retrieve the value in the network
            # Find the closest nodes to the value
            pass

        return

    async def handle_find_nodes_request(self, reader, writer, key: int):
        """
        This function returns to the sender the k closest nodes to a key located in its routing table.
        :param key:The key for which we want to find the closest nodes to this key.
        :param reader: The reader of the socket
        :param writer: The writer of the socket
        :return: True if the operation was successful.
        """

        # Get the address of the remote peer
        remote_address, remote_port = writer.get_extra_info("socket").getpeername()

        # Getting the closest nodes
        closest_nodes: list[NodeTuple] = self.local_node.routing_table.get_nearest_peers(key, NB_OF_CLOSEST_PEERS)
        nb_of_nodes_found = len(closest_nodes)

        NUMBER_OF_NODES_FIELD_SIZE = 2

        # Constructing response message
        message_size = int(SIZE_FIELD_SIZE
                           + MESSAGE_TYPE_FIELD_SIZE
                           + NUMBER_OF_NODES_FIELD_SIZE
                           + (KEY_FIELD_SIZE + IP_FIELD_SIZE + PORT_FIELD_SIZE) * nb_of_nodes_found)
        response = struct.pack(">HHH", message_size, DHT_FIND_NODE_RESP, nb_of_nodes_found)

        # Add each node information to the message
        for node in closest_nodes:
            # Add node ID field
            response += struct.pack("B" * KEY_FIELD_SIZE, node.node_id)
            # Add IP field
            ip_parts = map(int, node.ip_address.split())
            response += struct.pack(">BBBB", *ip_parts)
            # Add port field
            response += struct.pack(">H", node.port)

        # Send the response
        try:
            writer.write(response)
            await writer.drain()
        except Exception as e:
            print(f"[-] Failed to send DHT_FIND_NODE_RESP {e}")
            await bad_packet(reader, writer, data=response)
            return False
        print(f"[+] {remote_address}:{remote_port} <<< DHT_SUCCESS")
        return True

    async def handle_put_request(self):
        return


    #---------------------------------------------------------------------------------------------------------
    # Async functions that are not handler of received messages:
    #---------------------------------------------------------------------------------------------------------
    async def find_closest_nodes_in_network(self, key: int):

        closest_nodes : list[NodeTuple] = self.local_node.routing_table.get_nearest_peers(key, NB_OF_CLOSEST_PEERS)
        nodes_to_query : list[NodeTuple] = list(closest_nodes)

        # Definition of query message
        message_size = SIZE_FIELD_SIZE + MESSAGE_TYPE_FIELD_SIZE + KEY_FIELD_SIZE
        query = struct.pack(">HH", message_size, DHT_FIND_NODE)
        # TODO update pack thing below
        query += struct.pack(">", key)


        done = False
        # done = list to query is empty
        # add to list to query only when nodes getted are closer that to node quried
        while not done:
            pass
        for node in nodes_to_query:
            # query node
            # make connection
            # do it parallel and asynchronously
            # shit it will probably be complicated

            # list = result
            # TODO add filter to then sending message as well ?
            # filter_result : keep only nodes that are closer than the node itself
            pass
