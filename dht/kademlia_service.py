import secrets
import socket
import struct
import asyncio
import time

from local_node import LocalNode
from k_bucket import NodeTuple, ComparableNodeTuple
from asyncio.streams import StreamReader, StreamWriter
from constants import *
from xor_distance import key_distance

class KademliaService:

    def __init__(self, local_node: LocalNode):
        """
        Constructor
        :param local_node: A LocalNode object used to get access to the routing table and the local storage
        """
        self.local_node: LocalNode = local_node



    async def send_request(self, message_type: int, payload: bytes, host: str, port: int,
                           no_response_expected: bool = False) -> bytes:
        """
        This method is used to send a request to a remote peer.
        :param message_type: The request type number (int).
        :param payload: The content of the request.
        :param host: The IP address of the remote peer.
        :param port: The port of the remote peer.
        :param no_response_expected: if no response is expected after the request.
        :return: (bytes) containing the response of the request.
        """

        # Declaration of reader and writer
        reader: StreamReader
        writer: StreamWriter
        full_response = None

        try:
            # Establish connection with remote peer
            reader, writer = await asyncio.open_connection(host, port)

        except Exception as e:
            raise Exception(f"Connexion with remote peer failed: {e}")

        try:
            """
            Message Format
            +-----------------+----------------+---------------+---------------+
            |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
            +-----------------+----------------+---------------+---------------+
            |  Size           |  0             |  1            |  2            |
            +-----------------+----------------+---------------+---------------+
            |  Message type   |  2             |  3            |  2            |
            +-----------------+----------------+---------------+---------------+
            |  Node ID        |  4             |  35           |  32           |
            +-----------------+----------------+---------------+---------------+
            |  IP handler     |  36            | 39            | 4             |
            +-----------------+----------------+---------------+---------------+
            |  Port handler   |  40            | 41            | 2             |
            +-----------------+----------------+---------------+---------------+
            |  Body           |  42            | end           | -             |
            +-----------------+----------------+---------------+---------------+
            """


            # Determine the size of the message and create the size field
            size_of_message: int = (SIZE_FIELD_SIZE + MESSAGE_TYPE_FIELD_SIZE + KEY_SIZE + IP_FIELD_SIZE + PORT_FIELD_SIZE
                                    + len(payload))  # Total size including the size field

            size_field: bytes = struct.pack(">H", size_of_message)
            message_type_field: bytes = struct.pack(">H", message_type)
            node_id_field: bytes = self.local_node.node_id.to_bytes(32, byteorder='big')
            ip_handler_field: bytes = socket.inet_aton(self.local_node.handler_ip)
            port_handler_field: bytes = struct.pack(">H", self.local_node.handler_port)


            # Create full message
            full_message: bytes = (size_field + message_type_field + node_id_field + ip_handler_field
                                   + port_handler_field + payload)

            # Send the full message to the server
            writer.write(full_message)
            await writer.drain()  # Ensure the message is sent

            if no_response_expected:
                return "Message sent".encode()

            # Await response from the server
            response_size_bytes = await reader.read(SIZE_FIELD_SIZE)
            response_size: int = struct.unpack(">H", response_size_bytes)[0]
            response = await reader.read(response_size)
            full_response = response_size_bytes + response

        except Exception as e:
            raise Exception(f"Error while sending or receiving message: {e}")

        finally:
            writer.close()
            await writer.wait_closed()
            return full_response

    async def process_response(self, message: bytes):
        """
        This method extract the message type and the payload of a message
        :param message: the message payload (bytes)
        :return: the message type (int) and the payload (bytes)
        """
        if len(message) < SIZE_FIELD_SIZE + MESSAGE_TYPE_FIELD_SIZE:
            raise ValueError("Invalid response format, message too short")

        message_type = int(struct.unpack(">H", message[SIZE_FIELD_SIZE:SIZE_FIELD_SIZE + MESSAGE_TYPE_FIELD_SIZE])[0])

        payload = message[SIZE_FIELD_SIZE + MESSAGE_TYPE_FIELD_SIZE:]

        return message_type, payload


    async def handle_find_node_resp(self, message_type: int, payload: bytes, rpc_id: bytes) -> list[NodeTuple]:
        """
        This function is used to handle a find_node_resp
        :param message_type: the message type, should be FIND_NODE_RESP
        :param payload: the payload of the message
         :param rpc_id: The rpc_id of the request
        :return: true if the operation was successful, false otherwise
        """

        """
        Structure of body of FIND_NODE_RESP message
        +-----------------+----------------+---------------+---------------+
        |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
        +-----------------+----------------+---------------+---------------+
        |  RPC ID         |  0             |  15           |  16           |
        +-----------------+----------------+---------------+---------------+
        | nb_node_found   |  16            |  17           |  2            |
        +-----------------+----------------+---------------+---------------+
        | IP 1            |  18            |  -            |  4            |
        +-----------------+----------------+---------------+---------------+
        | port 1          |  -             |  -            |  2            |
        +-----------------+----------------+---------------+---------------+
        | node_id 1       |  -             |  -            |  32           |
        +-----------------+----------------+---------------+---------------+
        ...
        +-----------------+----------------+---------------+---------------+
        | IP n            |  -             |  -            |  4            |
        +-----------------+----------------+---------------+---------------+
        | port n          |  -             |  -            |  2            |
        +-----------------+----------------+---------------+---------------+
        | node_id n       |  -             |  -            |  32           |
        +-----------------+----------------+---------------+---------------+

        """

        if message_type == Message.FIND_NODE_RESP and payload[:RPC_ID_FIELD_SIZE] == rpc_id:
            index = RPC_ID_FIELD_SIZE
            nb_node_found = int.from_bytes(payload[index:index + NUMBER_OF_NODES_FIELD_SIZE], byteorder='big')
            index += NUMBER_OF_NODES_FIELD_SIZE
            list_of_nodes: list[NodeTuple] = []
            for i in range(nb_node_found):
                ip = socket.inet_ntoa(payload[index:index + IP_FIELD_SIZE])
                index += IP_FIELD_SIZE
                port = int.from_bytes(payload[index:index + PORT_FIELD_SIZE], byteorder='big')
                index += PORT_FIELD_SIZE
                node_id = int.from_bytes(payload[index:index + KEY_SIZE], byteorder='big')
                index += KEY_SIZE
                list_of_nodes.append(NodeTuple(ip, port, node_id))

            return list_of_nodes

        raise ValueError("Invalid FIND_NODE_RESP message content")

    async def send_find_node(self, host: str, port: int, key: int)->list[NodeTuple]:
        """
        This function is used to send a find request and to process the response
        :param host: the recipient IP address
        :param port: the port of the recipient
        :param key: the key to find the closest nodes to.
        :return: True if the response was valid.
        """

        """
        Body of FIND_NODE request 
        +-----------------+----------------+---------------+---------------+
        |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
        +-----------------+----------------+---------------+---------------+
        |  RPC ID         |  0             | 15            | 16            |
        +-----------------+----------------+---------------+---------------+
        |  key            |  16            | 46            | 32            |
        +-----------------+----------------+---------------+---------------+
        """

        rpc_id: bytes = secrets.token_bytes(RPC_ID_FIELD_SIZE)

        content = rpc_id + int.to_bytes(key, 32, byteorder='big')

        try:

            response = await self.send_request(Message.FIND_NODE, content, host, port)

        except Exception:
            return None

        message_type: int
        payload: bytes
        try:
            message_type, payload = await self.process_response(response)

        except Exception:
            return None

        try:
            return await self.handle_find_node_resp(message_type, payload, rpc_id)
        except Exception:
            return None



    async def find_closest_nodes_in_network(self, key: int) -> list[NodeTuple]:
        """
        This method is used to find the closest nodes to a key in the network. It will send multiple FIND_NODE request,
        until that it find the closest nodes.
        :param key: The key to find the closest node to.
        :return: the list of the closest nodes found in the network.
        """

        # The initial list of nodes to query is the k-closest nodes present in the local routing table.
        nodes_to_query: list[NodeTuple] = self.local_node.routing_table.get_nearest_peers(key, ALPHA)
        # The current list of closest nodes. It is represented as a heap.
        closest_nodes: list[ComparableNodeTuple] = [ComparableNodeTuple(node, key) for node in nodes_to_query]
        # A set to keep track of the already contacted nodes.
        contacted_nodes: set[NodeTuple] = set()

        # Send to each node
        tasks = [asyncio.create_task(self.send_find_node(node.ip_address, node.port, key)) for node in nodes_to_query]

        while tasks:

            done_tasks, pending_tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

            # For each response that we received we update
            # - the list of nodes to query
            # - the list of closest nodes
            # - the set of the already queried nodes

            for completed_task in done_tasks:
                k_closest_nodes_received : list[NodeTuple]= await completed_task
                if k_closest_nodes_received is not None:
                    for node in k_closest_nodes_received:
                        comparable_node = ComparableNodeTuple(node, key)
                        if node not in contacted_nodes:
                            contacted_nodes.add(node)  # add the node to contacted nodes.
                            # If the new node is closer than the closest in the list or if the list has less than k
                            # elements, add it
                            if len(closest_nodes) < K and node.node_id != self.local_node.node_id:
                                node_info: NodeTuple = comparable_node.nodeTuple
                                closest_nodes.append(comparable_node)
                                tasks.append(asyncio.create_task(self.send_find_node(node_info.ip_address,
                                                                                     node_info.port, key)))
                            elif all(comparable_node < n for n in closest_nodes) and node.node_id != self.local_node.node_id:
                                closest_nodes.remove(min(closest_nodes))
                                node_info: NodeTuple = comparable_node.nodeTuple
                                tasks.append(asyncio.create_task(self.send_find_node(node_info.ip_address,
                                                                                     node_info.port, key)))
            # Update the task list with pending tasks
            tasks = list(pending_tasks)

        # cleanup any and all tasks
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

        # return k closest nodes
        return [node.nodeTuple for node in sorted(closest_nodes)]

    async def send_store(self, host: str, port: int, key: int, ttl: int, value: bytes) -> None:
        """
        This function is used to send a store request
        :param host: the recipient IP address
        :param port: the port of the recipient
        :param key: The key associated with the value.
        :param ttl: The time-to-live of the value.
        :param value: The value to be stored.
        :return: True if the operation was successful, False otherwise
        """
        """
        Body of STORE request 
        +-----------------+----------------+---------------+---------------+
        |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
        +-----------------+----------------+---------------+---------------+
        |  RPC ID         |  0             | 15            | 16            |
        +-----------------+----------------+---------------+---------------+
        |  key            |  20            | 51            | 32            |
        +-----------------+----------------+---------------+---------------+
        |  TTL            |  52            | 53            |  2            |
        +-----------------+----------------+---------------+---------------+
        |  value          |  54            | end           |   variable    |
        +-----------------+----------------+---------------+---------------+
        """

        # Creation of the content of the request
        rpc_id: bytes = secrets.token_bytes(RPC_ID_FIELD_SIZE)

        content: bytes = rpc_id
        content += int.to_bytes(key, 32, byteorder='big')
        content += struct.pack(">H", ttl)
        content += value

        await self.send_request(Message.STORE, content, host, port, no_response_expected=True)

    async def store_value_in_network(self, key: int, ttl: int, value: bytes)->None:
        """
        This function store a value in the network. It will first identify which node need to store the value, and then
        it will send them a store instruction.
        :param replication: The number of time the value should be replicated
        :param key: the key associated to the value to be stored.
        :param ttl: the time to live of the value.
        :param value: the value to be stored.
        :return: nothing.
        """


        closest_nodes: list[NodeTuple] = await self.find_closest_nodes_in_network(key)

        # We check if our local node also need to store the value. This is the case if the local distance
        # to the key is smaller than the biggest distance of one node in the list or if we found less than k nodes in
        # the network.

        if len(closest_nodes) > 0 and key_distance(key, self.local_node.node_id) < key_distance(key, closest_nodes[-1].node_id):
            if len(closest_nodes) > K:
                closest_nodes.remove(closest_nodes[-1])
            async with self.local_node.local_hash_table_lock:
                self.local_node.local_hash_table.put(key, value, ttl)

        elif len(closest_nodes) < K:
            async with self.local_node.local_hash_table_lock:
                self.local_node.local_hash_table.put(key, value, ttl)

        for node in closest_nodes:
            await self.send_store(node.ip_address, node.port, key, ttl, value)


    async def send_find_value(self, host: str, port: int, key: int)->(bytes, list[NodeTuple]):
        """
        This method is used to send a find_value request in the network.
        :param host: the recipient IP address
        :param port: the port of the recipient
        :param key: The key associated with the value.
        :return:
        """

        """
        Body of FIND_VALUE request
        +-----------------+----------------+---------------+---------------+
        |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
        +-----------------+----------------+---------------+---------------+
        |  RPC ID         |  0             | 16            | 16            |
        +-----------------+----------------+---------------+---------------+
        |  key            |  17            | 48            |  32           |
        +-----------------+----------------+---------------+---------------+
        """

        # Creation of the content of the request
        rpc_id: bytes = secrets.token_bytes(RPC_ID_FIELD_SIZE)

        content: bytes = rpc_id
        content += int.to_bytes(key, 32, byteorder='big')
        response: bytes = await self.send_request(Message.FIND_VALUE, content, host, port)

        # If the response was invalid or not present we return None
        if not response:

            return None, None

        message_type: int
        payload: bytes

        try:
            message_type, payload = await self.process_response(response)

        except Exception:
            # If the response was invalid we return None
            return None, None

        # If a value was found, we process the body and return the value
        if message_type == Message.FIND_VALUE_RESP:
            """
            Body FIND_VALUE_RESP message
            +-----------------+----------------+---------------+---------------+
            |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
            +-----------------+----------------+---------------+---------------+
            |  RPC ID         |  0             |  15           |  16           |
            +-----------------+----------------+---------------+---------------+
            |  value          |  16            |  -            |  -            |
            +-----------------+----------------+---------------+---------------+
            """
            if rpc_id == payload[:RPC_ID_FIELD_SIZE]:
                value = payload[RPC_ID_FIELD_SIZE:]
                return value, None
            else:
                # If the rpc ID is invalid we return None
                return None, None

        # If the value was not found, but we received a list of closest node, we process it and return the list
        if message_type == Message.FIND_NODE_RESP:
            try:
                closest_nodes: list[NodeTuple] = await self.handle_find_node_resp(message_type, payload, rpc_id)
                return None, closest_nodes
            except Exception:
                return None, None

    async def find_value_in_network(self, key: int)-> bytes:
        """
        This method is used to find a value associated to a key in the distributed hash table.
        :param key: The key associated with the value that we are looking for.
        :return: The value if it was found.
        """

        # This method is very similar to the find_node method except that it stop when a value is found in the
        # network.

        # The initial list of nodes to query is the k-closest nodes present in the local routing table.
        nodes_to_query: list[NodeTuple] = self.local_node.routing_table.get_nearest_peers(key, ALPHA)

        # The current list of closest nodes. It is represented as a heap.
        closest_nodes: list[ComparableNodeTuple] = [ComparableNodeTuple(node, key) for node in nodes_to_query]
        # A set to keep track of the already contacted nodes.
        contacted_nodes: set[NodeTuple] = set()

        # Send to each node
        tasks = [asyncio.create_task(self.send_find_value(node.ip_address, node.port, key)) for node in nodes_to_query]
        contacted_nodes.update(nodes_to_query)
        # For each response that we received we update:
        # -the list of nodes to query
        # -the list of closest nodes
        # -the set of the already queried nodes
        while tasks:
            done_tasks, pending_tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            found_value = None
            new_tasks = []
            for task in done_tasks:
                # get the done tasks and look if we got a value matching with the key
                value, k_closest_nodes_received = task.result()

                if value:
                    found_value = value
                elif k_closest_nodes_received:
                    # if not the responding node will
                    for node in k_closest_nodes_received:
                        if node not in contacted_nodes and node.node_id != self.local_node.node_id:
                            contacted_nodes.add(node)
                            new_tasks.append(asyncio.create_task(self.send_find_value(node.ip_address, node.port, key)))


            if found_value:
                # Cancel and await all pending tasks quickly since value is found
                for task in pending_tasks:
                    task.cancel()
                await asyncio.gather(*pending_tasks, return_exceptions=True)
                # stop every task and return value
                return found_value
            # don't forget to update tasks for the loop
            tasks = new_tasks + list(pending_tasks)



    async def send_join_network(self, host: str, port: int)->bool:
        """

        :param host:
        :param port:
        :return:
        """

        """
        Body JOIN_NETWORK  message
        +-----------------+----------------+---------------+---------------+
        |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
        +-----------------+----------------+---------------+---------------+
        |  RPC ID         |  0             |  15           |  16           |
        +-----------------+----------------+---------------+---------------+
        """
        rpc_id: bytes = secrets.token_bytes(RPC_ID_FIELD_SIZE)

        try:

            response = await self.send_request(Message.JOIN_NETWORK,rpc_id, host, port)
        except Exception:
            print("Connection failed with known peer specified in routing table. Starting with empty routing table")
            return False

        message_type: int
        payload: bytes
        try:
            message_type, payload = await self.process_response(response)

        except Exception:
            print("Invalid response received from specified known peer. Starting with empty routing table")
            return False

        """
        Body JOIN_NETWORK_RESP message
        +-----------------+----------------+---------------+---------------+
        |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
        +-----------------+----------------+---------------+---------------+
        |  RPC ID         |  0             |  15           |  16           |
        +-----------------+----------------+---------------+---------------+
        |  Node ID        |  16            |  47           |  32           |
        +-----------------+----------------+---------------+---------------+
        """
        if message_type != Message.JOIN_NETWORK_RESP or len(payload) != RPC_ID_FIELD_SIZE + KEY_SIZE:
            print("Invalid response received from specified known peer. Starting with empty routing table")

            return False
        rpc_id_resp : bytes = payload[:RPC_ID_FIELD_SIZE]
        if rpc_id_resp != payload[:RPC_ID_FIELD_SIZE]:
            print("Invalid response received from specified known peer. Starting with empty routing table")

            return False

        node_id: int = int.from_bytes(payload[RPC_ID_FIELD_SIZE:], byteorder='big')

        async with self.local_node.routing_table_lock:
            self.local_node.routing_table.update_table(host, port, node_id)

        print(f"[+] Received JOIN_NETWORK_RESP, successfully joined the network with peer {node_id}")

        return True