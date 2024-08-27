<<<<<<< Updated upstream
# TODO add reguler api tests for the handler.
=======
# TODO add reguler api tests for the handler.
import time
import pytest
import os
from util import struct
from _pytest.fixtures import fixture

from MessageTypes import Message
from LocalNode import LocalNode

from dht_api_server import start_servers
from test.dht_api_client import client_run

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
        message_type = Message.DHT_PUT
        key = 1
        value = bytes(2)
        replication = 0
        tll = 0
        reserved = 0
        VALUE_SIZE = len(value)

        body = tll.to_bytes(TLL_SIZE, byteorder="big")
        body += replication.to_bytes(REPLICATION_SIZE, byteorder="big")
        body += reserved.to_bytes(1, byteorder="big")
        body += key.to_bytes(KEY_SIZE, byteorder="big")
        body += value
        #message =  header + body
        client_run(message_type, body, local_host, DHT_PORT ) # doesn't return anything.
        # but server should have it stored.
        hash_value = self.server_node.local_hash_table.get(key)
        assert hash_value == value

    def test_get_message(self):
        """
        test if DHT get message works.
        """
        # make message
        message_type = Message.DHT_PUT
        key = 1
        value = bytes(2)
        replication = 0
        reserved = 0
        ttl = 60
        self.server_node.local_hash_table.put(key,value,ttl)

        # now send the get messae
        message_type = Message.DHT_GET
        message_size = (SIZE_FIELD_SIZE
                        + MESSAGE_TYPE_FIELD_SIZE
                        + TLL_SIZE
                        + REPLICATION_SIZE
                        + 1  # reserved
                        + KEY_SIZE)
        #header = struct.pack(">HH", message_size, type)
        body = key.to_bytes(KEY_SIZE, byteorder="big")
        #message = header + body
        response = client_run(message_type, body, local_host, DHT_PORT)
        # shoudl be returning a dht_success message
        header = response[:4]
        size = header[:2]
        body = response[4:]

        # Extracting the message type
        size = struct.unpack(">H", header[:2])
        message_type = struct.unpack(">H", header[2:4])
        assert message_type == Message.DHT_SUCCESS
        response_key = int.from_bytes(body[:KEY_SIZE], byteorder="big")
        assert key == response_key
        response_value = body[KEY_SIZE:]
        assert value == response_value

    def test_time_to_live(self):
        key = 1
        value = bytes(2)

        ttl = 15
        self.server_node.local_hash_table.put(key, value, ttl)
        time.sleep(50)
        message_type = Message.DHT_GET
        body = key.to_bytes(KEY_SIZE, byteorder="big")
        # message = header + body
        response = client_run(message_type, body, local_host, DHT_PORT)
        # shoudl be returning a dht_success message
        header = response[:4]
        size = header[:2]
        body = response[4:]

        # Extracting the message type
        size = struct.unpack(">H", header[:2])
        message_type = struct.unpack(">H", header[2:4])
        assert message_type == Message.DHT_FAILURE
        response_key = int.from_bytes(body, byteorder="big")
        assert key == response_key
    def test_get_fail(self):
        key = 1
        value = bytes(2)

        ttl = 15
        type = Message.DHT_GET
        message_size = (SIZE_FIELD_SIZE
                        + MESSAGE_TYPE_FIELD_SIZE
                        + TLL_SIZE
                        + REPLICATION_SIZE
                        + 1  # reserved
                        + KEY_SIZE)
        # header = struct.pack(">HH", message_size, type)
        body = key.to_bytes(KEY_SIZE, byteorder="big")
        # message = header + body
        response = client_run(type, body, local_host, DHT_PORT)
        # shoudl be returning a dht_success message
        header = response[:4]
        size = header[:2]
        body = response[4:]

        # Extracting the message type
        size = struct.unpack(">H", header[:2])
        message_type = struct.unpack(">H", header[2:4])
        assert message_type == Message.DHT_FAILURE
        response_key = int.from_bytes(body, byteorder="big")
        assert key == response_key
if __name__ == "__main__":
    pytest.main()
>>>>>>> Stashed changes
