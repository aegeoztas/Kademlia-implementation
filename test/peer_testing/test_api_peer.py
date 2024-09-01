import asyncio
import struct
import random
import subprocess
import os
import requests
import pytest
import configparser
from cryptography.hazmat.primitives.asymmetric import rsa
from test.dht_api_client import send_message

"""
this test is for testing p2p interface of the dht implementation
"""
config = configparser.ConfigParser()

# Read the config.ini file
config.read('config.ini')


# Access values

async def gen_public_key():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    return private_key.public_key()


@pytest.fixture(scope="session", autouse=True)
def make_dht_docker():
    """
    Build and run an instance of dht-5 peer instance for testing
    """
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../run_docker.sh"))
    subprocess.run([script_path], check=True, shell=True)
    yield


@pytest.mark.asyncio
async def test_put():
    api_host = "127.0.0.1"
    api_port = 8889
    message_type = 650  #  dht put
    TTL_FIELD_SIZE = 2
    REPLICATION_FIELD_SIZE = 1
    RESERVED_FIELD_SIZE = 1
    ttl = int.to_bytes(100, TTL_FIELD_SIZE, byteorder='big')
    replication = int.to_bytes(2, REPLICATION_FIELD_SIZE, byteorder='big')
    reserved = int.to_bytes(0, RESERVED_FIELD_SIZE, byteorder='big')
    key = int.to_bytes(12345, 32, byteorder='big')
    value = b"12345"
    payload = ttl + replication + reserved + key + value

    result =  await send_message(message_type=message_type, payload=payload, host=api_host, port=api_port)
    print(result)
    input(result)


if __name__ == "__main__":
    pytest.run([])