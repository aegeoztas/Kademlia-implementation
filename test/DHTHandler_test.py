# TODO add reguler api tests for the handler.
import sys

import pytest
import os
from util import struct
from _pytest.fixtures import fixture

from MessageTypes import Message
from LocalNode import LocalNode

from dht_api_server import start_dht_server,start_kademlia_server,start_servers
from dht_api_client import send_message, send_ping, client_run

SIZE_FIELD_SIZE = int(os.getenv("SIZE_FIELD_SIZE"))
MESSAGE_TYPE_FIELD_SIZE = int(os.getenv("MESSAGE_TYPE_FIELD_SIZE"))
TLL_SIZE = int(os.getenv("TLL_SIZE"))
REPLICATION_SIZE = int(os.getenv("REPLICATION_SIZE"))
KEY_SIZE = int(os.getenv("KEY_SIZE"))
# Environment variables
DHT_PORT = 8890
KADEMLIA_PORT =  8889
local_host ="127.0.0.1"


class test_dht_handler():


    @fixture(scope='function')
    def start_server(self):
        server_node: LocalNode = start_servers()
        yield
    def test_put_message(self):
        # make message
        type = Message.DHT_PUT
        key = 1
        value = bytes(2)
        replication = 0
        reserved = 0
        VALUE_SIZE = len(value)
        message_size = (SIZE_FIELD_SIZE
                        + MESSAGE_TYPE_FIELD_SIZE
                        + TLL_SIZE
                        + REPLICATION_SIZE
                        + 1  # reserved
                        + KEY_SIZE
                        + VALUE_SIZE)
        #header = struct.pack(">HH", message_size, Message.FIND_NODE)
        body = key.to_bytes(KEY_SIZE, byteorder="big")
        body += value
        #message =  header + body
        client_run(type, body, local_host, DHT_PORT ) # doesn't return anything.
        # but server should have it stored.
        hash_value = self.server_node.local_hash_table.get(key)
        assert hash_value == value

    def test_get_message(self):
        """
        test if DHT get message works.
        """
        # make message
        type = Message.DHT_PUT
        key = 1
        value = bytes(2)
        replication = 0
        reserved = 0
        VALUE_SIZE = len(value)
        message_size = (SIZE_FIELD_SIZE
                        + MESSAGE_TYPE_FIELD_SIZE
                        + TLL_SIZE
                        + REPLICATION_SIZE
                        + 1  # reserved
                        + KEY_SIZE
                        + VALUE_SIZE)
        #header = struct.pack(">HH", message_size, Message.FIND_NODE)
        body = key.to_bytes(KEY_SIZE, byteorder="big")
        body += value
        #message = header + body
        client_run(type, body, local_host, DHT_PORT)  # doesn't return anything.
        # but server should have it stored.

        # now send the get messae
        type = Message.DHT_GET
        message_size = (SIZE_FIELD_SIZE
                        + MESSAGE_TYPE_FIELD_SIZE
                        + TLL_SIZE
                        + REPLICATION_SIZE
                        + 1  # reserved
                        + KEY_SIZE)
        #header = struct.pack(">HH", message_size, type)
        body = key.to_bytes(KEY_SIZE, byteorder="big")
        #message = header + body
        response = client_run(type, body, local_host, DHT_PORT)




    def get_from_kademlia(self):
        pass

    def test_get_success(self):
        pass

    def test_get_failiure(self):
        pass


if __name__ == "__main__":
    pytest.main()