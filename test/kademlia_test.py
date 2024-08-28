from k_bucket import NodeTuple
from kademlia_service import KademliaService
from local_node import LocalNode
import asyncio

async def main():
    IP = "127.0.0.1"
    PORT = 4444
    HOST_KEY_PEM = "test"

    local_node: LocalNode = LocalNode(IP, PORT, HOST_KEY_PEM)

    kademlia_service: KademliaService = KademliaService(local_node)

    TARGET_IP = "127.0.0.1"
    TARGET_PORT = 8888

    local_node.routing_table.update_table(TARGET_IP, TARGET_PORT, 4444)

    result = await kademlia_service.find_closest_nodes_in_network(0)

    for elem in result:
        print(elem)


if __name__ == "__main__":



    asyncio.run(main())