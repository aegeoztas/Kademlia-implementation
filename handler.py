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
async def handle_message(buf, reader, writer):
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
                return_status = await handle_ping(reader, writer)
            case DHT_PUT.value:
                return_status = await handle_put()
            case DHT_GET.value:
                return_status = await handle_get()
            case DHT_FIND_NODE.value:
                return_status = await handle_find_node()
            case DHT_STORE.value:
                ttl = struct.unpack(">H", body[0:1])
                replication = struct.unpack(">B", body[2])
                key = int.from_bytes(struct.unpack("B" * KEY_SIZE, buf[4: 4+KEY_SIZE-1]))
                value_length = len(body) - KEY_SIZE - 4
                value = struct.unpack("B" * value_length, buf[4+KEY_SIZE:])
                return_status = await handle_


                return_status = await handle_store(reader, writer)
            case _:
                await bad_packet(reader, writer,
                                 f"Unknown message type {message_type} received",
                                 header)
    except Exception as e:
        await bad_packet(reader, writer, f"Wrongly formatted message", buf)
    return return_status


async def handle_ping(reader, writer):
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


async def handle_store():


async def handle_get():
    return


async def handle_put():
    return


async def handle_find_node():
    return



