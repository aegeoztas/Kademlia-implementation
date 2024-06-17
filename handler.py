import random
import argparse
import asyncio
from socket import AF_INET
from LocalNode import LocalNode
from network.messages import *
from util import *
from network.Kademlia import GET, PUT, SUCCESS, FAILURE
from network.Network import Connection

DHT_ADDR = "127.0.0.1"
DHT_PORT = 7401

SIZE_FIELD_SIZE = 2
MESSAGE_TYPE_FIELD_SIZE = 2
KEY_SIZE = 256


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
                    key = int.from_bytes(struct.unpack("B" * KEY_SIZE, buf[5: 5 + KEY_SIZE -1]))
                    return_status = await self.handle_get(reader, writer, key)
                case DHT_FIND_NODE.value:
                    return_status = await handle_find_node()
                case DHT_STORE.value:
                    ttl = int(struct.unpack(">H", body[0:1]))
                    replication = int(struct.unpack(">B", body[2]))
                    key = int.from_bytes(struct.unpack("B" * KEY_SIZE, buf[4: 4 + KEY_SIZE - 1]), byteorder="big")
                    value_field_size = len(body) - KEY_SIZE - 4
                    value = struct.unpack("B" * value_field_size, buf[4 + KEY_SIZE:])
                    return_status = await self.handle_store(ttl, key, value)
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

    async def handle_store(self, ttl: int, key: int, value: bytes):
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


    async def handle_get(self, reader, writer, key: int):
        """
        This method handles a get message. It the local node contains the data,
        it will simply return it. If not, it will try to get from the network.
        :param reader: The reader of the socket.
        :param writer: The writer of the socket.
        :param key: The key associated to the data.
        :return: True if the operation was successful.
        """
        value = self.local_node.local_hash_table.get(key)
        if value is not None: # TODO check syntax
            # return value to the requester
            # Define the DHT Success message
            message_size = int(SIZE_FIELD_SIZE + MESSAGE_TYPE_FIELD_SIZE
                               + KEY_SIZE + len(value))
            response = struct.pack(">HH", message_size,
                                   DHT_SUCCESS)
            response += key
            response += value
            # Send

        else:
            # Query value

        return

    async def handle_put():
        return

    async def handle_find_node():
        return
