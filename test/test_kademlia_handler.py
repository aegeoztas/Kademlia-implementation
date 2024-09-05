# File need to be placed in the DHT folder in order for the tests to work.
import asyncio
import struct
from cryptography.hazmat.primitives.asymmetric import rsa
import random

from local_node import LocalNode
from kademlia_service import KademliaService

SERVER_UNDER_TEST_IP = "127.0.0.1"
SERVER_UNDER_TEST_PORT = 8890

API_UNDER_TEST_IP = "127.0.0.1"
API_UNDER_TEST_PORT = 8889

async def gen_public_key():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    return private_key.public_key()


async def get_service_with_random_infos():
    public_key = await gen_public_key()
    local_node: LocalNode = LocalNode("1.1.1.1", random.randint(0, 50), public_key)
    service: KademliaService = KademliaService(local_node)
    return service


async def store_and_retrieve_test():
    # work with any server
    public_key = await gen_public_key()
    local_node: LocalNode = LocalNode("1.1.1.1", 0, public_key)
    service: KademliaService = KademliaService(local_node)

    value = "test1value".encode()
    ttl = 100
    key = 12345
    await service.send_store(SERVER_UNDER_TEST_IP, SERVER_UNDER_TEST_PORT, key, ttl, value)



    public_key = await gen_public_key()
    local_node: LocalNode = LocalNode("2.2.2.2", 0, public_key)
    service: KademliaService = KademliaService(local_node)

    key = 12345

    value_retrieved, nodes = await service.send_find_value(SERVER_UNDER_TEST_IP, SERVER_UNDER_TEST_PORT, key)

    assert nodes is None
    assert value_retrieved == value

async def test_find_nodes():
    # need to be run just after server startup and with server with 0 known peer
    service1 = await get_service_with_random_infos()
    service2 = await get_service_with_random_infos()
    service3 = await get_service_with_random_infos()

    key1 = random.randint(0, 100)
    value1 = struct.pack(">I", random.randint(0, 50))
    await service1.send_store(SERVER_UNDER_TEST_IP, SERVER_UNDER_TEST_PORT, key1, 100, value1)

    key2 = random.randint(0, 100)
    value2 = struct.pack(">I", random.randint(0, 50))
    await service2.send_store(SERVER_UNDER_TEST_IP, SERVER_UNDER_TEST_PORT, key2, 100, value2)

    key3 = random.randint(0, 100)
    value3 = struct.pack(">I", random.randint(0, 50))
    await service3.send_store(SERVER_UNDER_TEST_IP, SERVER_UNDER_TEST_PORT, key3, 100, value3)

    resp = await service3.send_find_node(SERVER_UNDER_TEST_IP, SERVER_UNDER_TEST_PORT, 0)

    assert len(resp) == 3

    for elem in resp:
        assert elem.node_id == service1.local_node.node_id or elem.node_id == service2.local_node.node_id or elem.node_id == service3.local_node.node_id
        print(elem)



async def test_find_value_with_no_value():
    # need to be run just after server startup and with server with 0 known peer
    service1 = await get_service_with_random_infos()
    service2 = await get_service_with_random_infos()
    service3 = await get_service_with_random_infos()

    key1 = random.randint(0, 100)
    value1 = struct.pack(">I", random.randint(0, 50))
    await service1.send_store(SERVER_UNDER_TEST_IP, SERVER_UNDER_TEST_PORT, key1, 100, value1)

    key2 = random.randint(0, 100)
    value2 = struct.pack(">I", random.randint(0, 50))
    await service2.send_store(SERVER_UNDER_TEST_IP, SERVER_UNDER_TEST_PORT, key2, 100, value2)

    key3 = random.randint(0, 100)
    value3 = struct.pack(">I", random.randint(0, 50))
    await service3.send_store(SERVER_UNDER_TEST_IP, SERVER_UNDER_TEST_PORT, key3, 100, value3)

    nothing, resp = await service3.send_find_value(SERVER_UNDER_TEST_IP, SERVER_UNDER_TEST_PORT, 0)

    assert nothing is None
    assert len(resp) == 3

    for elem in resp:
        assert elem.node_id == service1.local_node.node_id or elem.node_id == service2.local_node.node_id or elem.node_id == service3.local_node.node_id
        print(elem)

async def test_join():
    # work with any server
    public_key = await gen_public_key()
    local_node: LocalNode = LocalNode("1.1.1.1", 0, public_key)
    service: KademliaService = KademliaService(local_node)

    assert await service.send_join_network(SERVER_UNDER_TEST_IP, SERVER_UNDER_TEST_PORT)

    assert len(service.local_node.routing_table.get_nearest_peers(0, 1)) == 1

async def main():
    # Each test should be run alone and with a fresh server without known peers
    await store_and_retrieve_test()
    # await test_join()
    # await test_find_nodes()
    # await test_find_value_with_no_value()






if __name__ == "__main__":
    asyncio.run(main())
