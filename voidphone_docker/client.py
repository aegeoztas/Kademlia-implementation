import asyncio
import argparse
import struct
import time
import secrets
import hexdump
import configparser


DHT_PUT = 650
DHT_GET = 651
DHT_SUCCESS = 652
DHT_FAILURE = 653

"""
This file simply copies what dht client under voidphone does and implements
it on a docker machine With docker files and bash script. it uses 
"""
async def send_get(writer, reader, dht_key):
    getreq = struct.pack(">HH32s", int((32+256)/8), DHT_GET, dht_key)
    print("[+] Sending GET request...")
    try:
        writer.write(getreq)
        await writer.drain()
    except Exception as e:
        print(f"[-] Sending of packet failed: {e}.")
        return False

    buf = await reader.read(4096)
    if buf == b'':
        print('[-] Connection closed by other endpoint.')
        return False

    try:
        asize, atype = struct.unpack(">HH", buf[:4])
        akey = buf[4:int(256/8)+4]

        if atype == DHT_SUCCESS:
            avalue = buf[int(256/8)+4:]
            print(f"[+] Received DHT_SUCCESS."
                  + f" size: {asize}, key: {akey}, value: {avalue}")
        elif atype == DHT_FAILURE:
            print(f"[+] Received DHT_FAILURE."
                  + f" size: {asize}, key: {akey}")
        else:
            print("[-] Received unexpected answer")
            hexdump.hexdump(buf)
    except Exception as e:
        print(f"[-] Parsing of packet failed: {e}.")
        hexdump.hexdump(buf)

    return True

async def send_put(writer, dht_key, dht_value):
    putreq = struct.pack(">HHHBB",
                         (4+4+int(256/8)+len(dht_value)),
                         DHT_PUT,
                         100,
                         1,
                         0)
    putreq += dht_key
    putreq += dht_value

    print("[+] Sending PUT request...")
    print("put value " )
    print(dht_value)
    print("send put request: ")
    hexdump.hexdump(putreq)
    try:
        writer.write(putreq)
        await writer.drain()
    except Exception as e:
        print(f"[-] Sending of packet failed: {e}.")
        return False

    return True

async def get_socket(host, port):
    print(f"Trying to connect to {host}:{port}")
    reader, writer = await asyncio.open_connection(host, port)
    return reader, writer

async def main():
    # parse commandline arguments
    config = configparser.ConfigParser()
    config.read('/DHT5/configuration/config_5.ini')
    # Read configuration for the first server (PUT request)
    put_api_host, api_port = config.get('dht', 'api_address').split(':')
    put_api_port = int(api_port)
    # Read configuration for the second server (GET request)#

    config.read('/DHT5/configuration/config_1.ini')
    get_api_host, api_port = config.get('dht', 'api_address').split(':')
    get_api_port = int(api_port)

    # Key and Value to use
    dht_key  = secrets.token_bytes(32) # 32 bytes key
    dht_value = b'sample_value'

    # Connect to the first server and send PUT request
    print(f"[log] client trying to put value into {put_api_host}")
    put_reader, put_writer = await get_socket(put_api_host, put_api_port)
    await send_put(put_writer, dht_key, dht_value)
    print(f"[log] put successful")
    # Connect to the second server and send GET request
    print("[log] client sleeps for 10 seconds ")
    time.sleep(10)
    print(f"[log] client trying to get value from {get_api_host}")
    get_reader, get_writer = await get_socket(get_api_host, get_api_port)
    await send_get(get_writer, get_reader, dht_key)
    print(f"[log] get successful")
    # Clean up
    put_writer.close()
    get_writer.close()
    await put_writer.wait_closed()
    await get_writer.wait_closed()



if __name__ == '__main__':
    asyncio.run(main())