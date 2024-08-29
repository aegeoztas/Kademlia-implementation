import asyncio
import sys
import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

from dht.k_bucket import NodeTuple
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



async def send_store_test():

    public_key = await gen_public_key()
    local_node: LocalNode = LocalNode("1.1.1.1", 0, public_key)
    service: KademliaService = KademliaService(local_node)

    value = "test1value".encode()
    ttl = 100
    key = 12345
    await service.send_store(SERVER_UNDER_TEST_IP, SERVER_UNDER_TEST_PORT, key, ttl, value)

    # using debugger to check if other process stored the value





async def main():
    await send_store_test()






if __name__ == "__main__":
    asyncio.run(main())
