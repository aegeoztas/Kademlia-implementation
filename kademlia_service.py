import heapq
import secrets

import LocalNode
import asyncio
from LocalNode import LocalNode
from k_bucket import NodeTuple
from util import *
from asyncio.streams import StreamReader, StreamWriter
from Constants import *
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

        size = int(struct.unpack(">H", message[:SIZE_FIELD_SIZE])[0])
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

        except Exception as e:
            return None

        message_type: int = 0
        payload: bytes
        try:
            message_type, payload = await self.process_response(response)

        except Exception as e:
            return None

        try:
            return await self.handle_find_node_resp(message_type, payload, rpc_id)
        except Exception as e:
            return None



    async def find_closest_nodes_in_network(self, key: int) -> list[NodeTuple]:
        """
        This method is used to find the closest nodes to a key in the network. It will send multiple FIND_NODE request,
        until that it find the closest nodes.
        :param key: The key to find the closest node to.
        :return: the list of the closest nodes found in the network.
        """

        class ComparableNodeTuple:
            # This class is used to compare two NodeTuple. A NodeTuple with a smaller distance to a specific key
            # is considered greater than the other with a bigger distance.

            def __init__(self, node_tuple: NodeTuple, reference_key: int):
                self.nodeTuple: NodeTuple = node_tuple
                self.reference_key: int = reference_key

            def __lt__(self, other):
                # Nodes are compared with distance

                return key_distance(self.nodeTuple.node_id, self.reference_key) < key_distance(other.nodeTuple.node_id,
                                                                                               self.reference_key)

        # The initial list of nodes to query is the k-closest nodes present in the local routing table.
        nodes_to_query: list[NodeTuple] = self.local_node.routing_table.get_nearest_peers(key, NB_OF_CLOSEST_PEERS)
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
                            if len(closest_nodes) < K:
                                node_info: NodeTuple = comparable_node.nodeTuple
                                closest_nodes.append(comparable_node)
                                tasks.append(asyncio.create_task(self.send_find_node(node_info.ip_address,
                                                                                     node_info.port, key)))
                            elif all(comparable_node < n for n in closest_nodes):
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

# async def handle_store_request(self, replication: int, ttl: int, key: int, value: bytes):
#     """
#     This function handles a store message. If this function is called, this node has been designated to store a value.
#     It must then store the value in its storage.
#     :param reader: The reader of the socket.
#     :param replication: the number of times that this key,value pair should be replicated through the network.
#     :param ttl: The time to live of the value to be stored.
#     :param key: The 256 bit key associated to the value.
#     :param value: The value to be stored.
#     :return: True if the operation was successful.
#     """
#     if ttl == 0:
#         # it is forbiden to have 0 ttl so we drop the request
#         return False
#     elif ttl> MAXTTL:
#         ttl = MAXTTL
#
#     self.local_node.local_hash_table.put(key, value, ttl)
#
#     if replication == 0:
#         return True
#     elif replication > MAXREPLICATION:
#         replication = MAXREPLICATION
#         #here the replication is only a hint and too much of it can be bad.
#         # so we set cap on it.
#     self.republish_store_request(replication,ttl,key,value)
#     return True

#
#     async def republish_store_request(self, replication: int, ttl: int, key: int, value: bytes):
#         """
#         this function gets the leftovers from handle_store_function and
#         tries to replicate the storage evenly as possible.
#         """
#
#         # TODO add key mixing to this function so each repub has a different key for the same value
#         # then on our local bucket send closest places
#         nodes_to_store: list[NodeTuple] = self.local_node.routing_table.get_nearest_peers(key, NB_OF_CLOSEST_PEERS)
#         # both depth wise(how many hops to last) AND width wise (how many paralel hops).
#         # also replication might also be used to tell how many times same key should be used.
#         # like maybe use different keys
#
#         tasks = []
#         if nodes_to_store:
#             # Calculate how much each node should replicate.
#             base_rep = replication // len(nodes_to_store)  # use floor division 8 // 3 = 2
#             extra = replication % len(nodes_to_store)  # 8 % 3 = 2
#             # so for 8 repetition among 3 nodes we would add +1 to first 2 nodes
#
#             # Generate tasks for sending store messages.
#             tasks = []
#             for i, node in enumerate(nodes_to_store):
#                 # Distribute the 'extra' replications across the first 'extra' nodes.
#                 if i < extra:
#                     rep_to_send = base_rep + 1
#                 else:
#                     rep_to_send = base_rep
#
#                 tasks.append(self.send_store_message(node, rep_to_send, ttl, key, value))
#

#     async def handle_find_value_request(self, reader, writer, key: int):
#         """
#         This function finds if it has the key asked.
#         if not returns to the sender the k closest nodes to the key,that is located in its routing table.
#         :param key:The key for which we want to find.
#         :param reader: The reader of the socket
#         :param writer: The writer of the socket
#         :return: True if the operation was successful. Kbucket of known nodes if it doesn't have it
#         """
#
#         """
#         FIND_VALUE response format
#
#
#         Message Format
#         +-----------------+----------------+---------------+---------------+
#         |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
#         +-----------------+----------------+---------------+---------------+
#         |  Size           |  0             |  1            |  2            |
#         +-----------------+----------------+---------------+---------------+
#         |  Message type   |  2             |  3            |  2            |
#         +-----------------+----------------+---------------+---------------+
#         |  Body           |  3             | end           | Size -4       |
#         +-----------------+----------------+---------------+---------------+
#
#
#
#         """
#         value = self.local_node.local_hash_table.get(key)
#         if value != None:
#             # if value is existing send it back
#             message_size = int(SIZE_FIELD_SIZE
#                            + MESSAGE_TYPE_FIELD_SIZE
#                            + sys.getsizeof(value) )
#             header = struct.pack(">HH", message_size, Message.FIND_VALUE_SUCCESS)
#             body = key.to_bytes(KEY_SIZE, byteorder="big")
#             #  same as DHT_SUCCESS message return key
#             if type(value) == bytes:
#                 body += value # AND value
#             else:
#                 body += value.to_bytes(KEY_SIZE, byteorder="big")
#             response = header + body
#             try:
#                 writer.write(response)
#                 await writer.drain()
#             except Exception as e:
#                 print(f"[-] Failed to send FIND_VALUE_SUCCESS {e}")
#                 await bad_packet(reader, writer, data=response)
#                 return False
#         else:
#             # else this acts as handle_find_nodes_request
#
#             return self.handle_find_nodes_request(reader,writer,key)
#

#

#     async def send_find_value_message(self, recipient: NodeTuple,value: bytes):
#         """
#         sends FIND_VALUE message of the Kademlia.
#         This method is responsible for sending a find value message.
#         SIMILAR TO DHT_GET message.
#         :param key: The key used to find the closest nodes.
#         :param recipient: A node tuple that represents the peer to which the message will be sent.
#         :return: True if the operation was successful.
#         """
#
#
#         """
#         Structure of FIND_NODE query
#         +-----------------+----------------+---------------+---------------+
#         |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
#         +-----------------+----------------+---------------+---------------+
#         |  size           |  0             |  1            |  2            |
#         +-----------------+----------------+---------------+---------------+
#         |  FIND_VALUE     |  2             |  3            |  2            |
#         +-----------------+----------------+---------------+---------------+
#         |  key            |  4             |  259          |  256          |
#         +-----------------+----------------+---------------+---------------+
#         """
#
#         message_size = SIZE_FIELD_SIZE + MESSAGE_TYPE_FIELD_SIZE + KEY_SIZE
#         header = struct.pack(">HH", message_size, Message.FIND_NODE)
#         body = value
#         query = header+body
#         # Make the connection to the remote peer
#         ip: str = recipient.ip_address
#         port: int = recipient.port
#         connection: Connection = Connection(ip, port, TIMEOUT)
#         if await connection.connect() and await connection.send_message(query):
#             message_type_response, body_response = await connection.receive_message()
#         else:
#             await connection.close()
#             return False
#         # Verify that the response has the correct format.
#         if message_type_response is None or body_response is None or message_type_response != Message.FIND_NODE_RESP:
#             print("Failed to get DHT_FIND_NODE_RESP")
#             await connection.close()
#             return False
#         else:
#             # We first close the socket
#             await connection.close()
#             """
#             Structure of DHT_FIND_NODE_RESP body message
#             +-----------------+----------------+---------------+---------------+
#             |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
#             +-----------------+----------------+---------------+---------------+
#             |  nb_of_nodes    |  0             |  1            |  2            |
#             +-----------------+----------------+---------------+---------------+
#             |  key_node_1     |  2             |  33           |  32           |
#             +-----------------+----------------+---------------+---------------+
#             |  ip_node_1      |  34            |  37           |  4            |
#             +-----------------+----------------+---------------+---------------+
#             |  port_node_1    |  38            |  40           |  2            |
#             +-----------------+----------------+---------------+---------------+
#             ...
#             |  key_node_n     |  ...           |  ...          |  32           |
#             +-----------------+----------------+---------------+---------------+
#             |  ip_node_n      |  ...           |  ...          |  4            |
#             +-----------------+----------------+---------------+---------------+
#             |  port_node_n    |  ...           |  ...          |  2            |
#             +-----------------+----------------+---------------+---------------+
#             """
#             # Extracting the fields of the message
#             try:
#                 list_of_returned_nodes: list[NodeTuple] = list()
#                 nb_of_nodes: int = struct.unpack(">H", body_response[0:3])
#                 read_head = 3
#                 for i in range(nb_of_nodes):
#                     key_node: int = int.from_bytes(body_response[read_head:read_head + KEY_SIZE - 1], byteorder="big")
#                     read_head += KEY_SIZE
#                     ip_node: str = socket.inet_ntoa(body_response[read_head:read_head + IP_FIELD_SIZE - 1])
#                     read_head += IP_FIELD_SIZE
#                     port_node: int = struct.unpack(">H", body_response[read_head:read_head + PORT_FIELD_SIZE - 1])
#                     read_head += PORT_FIELD_SIZE
#                     received_node = NodeTuple(ip_node, port_node, key_node)
#                     list_of_returned_nodes[i] = received_node
#
#                 return list_of_returned_nodes
#
#             except Exception as e:
#                 print("Body of the response has the wrong format")
#                 return None
#     async def send_find_closest_nodes_message(self, recipient: NodeTuple, key: int) -> list[NodeTuple]:
#         """
#         FIND_NODES message of the Kademlia.
#         This method is responsible for sending a find node message.
#         :param key: The key used to find the closest nodes.
#         :param recipient: A node tuple that represents the peer to which the message will be sent.
#         :return: True if the operation was successful.
#         """
#         # Definition of FIND_NODES query
#         """
#         Structure of FIND_NODES query
#         +-----------------+----------------+---------------+---------------+
#         |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
#         +-----------------+----------------+---------------+---------------+
#         |  size           |  0             |  1            |  2            |
#         +-----------------+----------------+---------------+---------------+
#         |  FIND_NODES     |  2             |  3            |  2            |
#         +-----------------+----------------+---------------+---------------+
#         |  key            |  4             |  259          |  256          |
#         +-----------------+----------------+---------------+---------------+
#         """
#         message_size = SIZE_FIELD_SIZE + MESSAGE_TYPE_FIELD_SIZE + KEY_SIZE
#         query = struct.pack(">HH", message_size, Message.FIND_NODE)
#         query += key.to_bytes(KEY_SIZE, byteorder="big")
#
#         # Make the connection to the remote peer
#         ip: str = recipient.ip_address
#         port: int = recipient.port
#         connection: Connection = Connection(ip, port, TIMEOUT)
#         if await connection.connect() and await connection.send_message(query):
#             message_type_response, body_response = await connection.receive_message()
#         else:
#             await connection.close()
#             return False
#         # Verify that the response has the correct format.
#         if message_type_response is None or body_response is None or message_type_response != Message.FIND_NODE_RESP:
#             print("Failed to get DHT_FIND_NODE_RESP")
#             await connection.close()
#             return False
#         else:
#             # We first close the socket
#             await connection.close()
#             """
#             Structure of DHT_FIND_NODE_RESP body message
#             +-----------------+----------------+---------------+---------------+
#             |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
#             +-----------------+----------------+---------------+---------------+
#             |  nb_of_nodes    |  0             |  1            |  2            |
#             +-----------------+----------------+---------------+---------------+
#             |  key_node_1     |  2             |  33           |  32           |
#             +-----------------+----------------+---------------+---------------+
#             |  ip_node_1      |  34            |  37           |  4            |
#             +-----------------+----------------+---------------+---------------+
#             |  port_node_1    |  38            |  40           |  2            |
#             +-----------------+----------------+---------------+---------------+
#             ...
#             |  key_node_n     |  ...           |  ...          |  32           |
#             +-----------------+----------------+---------------+---------------+
#             |  ip_node_n      |  ...           |  ...          |  4            |
#             +-----------------+----------------+---------------+---------------+
#             |  port_node_n    |  ...           |  ...          |  2            |
#             +-----------------+----------------+---------------+---------------+
#             """
#             # Extracting the fields of the message
#             try:
#                 list_of_returned_nodes : list[NodeTuple] = list()
#                 nb_of_nodes: int = struct.unpack(">H", body_response[0:3])
#                 read_head = 3
#                 for i in range(nb_of_nodes):
#                     key_node: int = int.from_bytes(body_response[read_head:read_head+KEY_SIZE-1], byteorder="big")
#                     read_head += KEY_SIZE
#                     ip_node: str = socket.inet_ntoa(body_response[read_head:read_head + IP_FIELD_SIZE-1])
#                     read_head += IP_FIELD_SIZE
#                     port_node: int = struct.unpack(">H", body_response[read_head:read_head+PORT_FIELD_SIZE-1])
#                     read_head += PORT_FIELD_SIZE
#                     received_node = NodeTuple(ip_node, port_node, key_node)
#                     list_of_returned_nodes[i] = received_node
#
#                 return list_of_returned_nodes
#
#             except Exception as e:
#                 print("Body of the response has the wrong format")
#                 return None
#
#     async def send_store_message(self,recipient: NodeTuple, replication: int, ttl: int, key: int, value: bytes):
#
#
#         """
#                sends STORE message of the Kademlia.
#                This method is responsible for sending a find value message.
#                SIMILAR TO DHT_PUT message.
#                :param key: The key used to find the closest nodes.
#                :param recipient: A node tuple that represents the peer to which the message will be sent.
#                :return: True if the operation was successful.
#                """
#
#         """
#         Structure of STORE MESSAGE
#         +-----------------+----------------+---------------+---------------+
#         |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
#         +-----------------+----------------+---------------+---------------+
#         |  size           |  0             |  1            |  2            |
#         +-----------------+----------------+---------------+---------------+
#         |  STORE          |  2             |  3            |  2            |
#         +-----------------+----------------+---------------+---------------+
#         |  TTL            |  4             |  5            |  2            |
#         +-----------------+----------------+---------------+---------------+
#         |  replication    |  6             |  6            |  1            |
#         +-----------------+----------------+---------------+---------------+
#         |  reserved       |  7             |  7            |  1            |
#         +-----------------+----------------+---------------+---------------+
#         |  key            |  8             |  39           |  32           |
#         +-----------------+----------------+---------------+---------------+
#         |  value          |  40            |  end          |  variable     |
#         +-----------------+----------------+---------------+---------------+
#         """
#
#         message_size = (SIZE_FIELD_SIZE
#                         + MESSAGE_TYPE_FIELD_SIZE
#                         + TLL_SIZE
#                         + REPLICATION_SIZE
#                         + 1
#                         + KEY_SIZE)
#         header = struct.pack(">HH", message_size, Message.FIND_NODE)
#         body = key.to_bytes(KEY_SIZE, byteorder="big")
#         body += value
#         query = header + body
#         # Make the connection to the remote peer
#         ip: str = recipient.ip_address
#         port: int = recipient.port
#         connection: Connection = Connection(ip, port, TIMEOUT)
#         await connection.connect()
#         await connection.send_message(query)
#         # there is no need to verify response to a store message
#         await connection.close()
#
#
# class DHTHandler:
#     """
#     The role of this class is to handle incoming messages that are
#     reaching the local node and using DHT API
#     """
#
#     def __init__(self, local_node: LocalNode, kademlia_handler: KademliaHandler):
#         # self.local_node: LocalNode = local_node
#         # it doesn't make sense for dht handler to have it's own local node
#         self.k_handler = kademlia_handler
#         """
#
#         Constructor
#         :param local_node: A LocalNode object used to get access to the routing table and the local storage
#
#         """
#
#     async def handle_message(self, buf: bytes, reader: StreamReader, writer: StreamWriter):
#         """
#         This function handles incoming requests according to their content.
#         :param buf: A buffer of bytes containing the content of the message.
#         :param reader: The StreamReader of the socker.
#         :param writer: The StreamWriter of the socket.
#         :return: True if the operation was successful.
#         """
#
#         """
#         Message Format
#         +-----------------+----------------+---------------+---------------+
#         |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
#         +-----------------+----------------+---------------+---------------+
#         |  Size           |  0             |  1            |  2            |
#         +-----------------+----------------+---------------+---------------+
#         |  Message type   |  2             |  3            |  2            |
#         +-----------------+----------------+---------------+---------------+
#         |  Body           |  3             | end           | Size -4       |
#         +-----------------+----------------+---------------+---------------+
#         """
#         # Extracting header and body of the message
#         header = buf[:4]
#         body = buf[4:]
#
#         # Extracting the message type
#         message_type = struct.unpack(">HH", header[2:4])
#
#         return_status = False
#
#         # A specific handler is called depending on the message type.
#         try:
#             match message_type:
#                 # DHT API Messages
#                 case Message.DHT_GET:
#                     """
#                     Body of DHT_GET
#                     +-----------------+----------------+---------------+---------------+
#                     |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
#                     +-----------------+----------------+---------------+---------------+
#                     |  key            |  0             |  31           |  32           |
#                     +-----------------+----------------+---------------+---------------+
#                     """
#                     key = int.from_bytes(body[0: KEY_SIZE - 1])
#                     return_status = await self.handle_get_request(reader, writer, key)
#
#                 case Message.DHT_PUT:
#                     """
#                     Body of DHT_PUT
#                     +-----------------+----------------+---------------+---------------+
#                     |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
#                     +-----------------+----------------+---------------+---------------+
#                     |  ttl            |  0             |  1            |  2            |
#                     +-----------------+----------------+---------------+---------------+
#                     |  replication    |  2             |  2            |  1            |
#                     +-----------------+----------------+---------------+---------------+
#                     |  reserved       |  3             |  3            |  1            |
#                     +-----------------+----------------+---------------+---------------+
#                     |  key            |  4             |  35           |  32           |
#                     +-----------------+----------------+---------------+---------------+
#                     |  value          |  36            |  end          |  variable     |
#                     +-----------------+----------------+---------------+---------------+
#                     """
#                     ttl: int = int.from_bytes(struct.pack(">H", body[0:2]))
#                     replication: int = body[2]
#                     key: int = int.from_bytes(body[4:4 + KEY_SIZE - 1], byteorder="big")
#                     value: bytes = body[260:]
#                     return_status = await self.handle_put_request(reader, writer, ttl, replication, key, value)
#
#                 case _:
#                     await bad_packet(reader, writer,
#                                      f"Unknown message type {message_type} received",
#                                      header)
#
#         except Exception as e:
#             await bad_packet(reader, writer, f"Wrongly formatted message", buf)
#         return return_status
#
#     async def handle_get_request(self, reader, writer, key: int):
#         """
#         This method handles a get message. If the local node contains the data,
#         it will simply return it. If not, it will try to get from the kademlia network.
#         if it cant find it returns DHT_Success or DHT_failiure
#         :param reader: The reader of the socket.
#         :param writer: The writer of the socket.
#         :param key: The key associated to the data.
#         :return: True if the operation was successful.
#         """
#         # Get the address of the remote peer
#         remote_address, remote_port = writer.get_extra_info("socket").getpeername()
#
#         # Check if the value is in the local storage
#         value = self.local_node.local_hash_table.get(key)
#
#         # If the value is not in the local storage, we have to get it from the Kademlia network from the other peers.
#         if value is None:
#
#             # needs to send a kademlia get message.
#             # better to start working there
#             find_value_response = await self.k_handler.handle_find_value_request(reader, writer, key)
#             # this way as we pass the reader / writer this will be handled on kademlia interface
#             # kademlia handler will act as it got FIND_VALUE request
#             # if it finds the value it returns true and sends the key value pair back to the passed reader/writer
#             # as we use same message types for dht_get-find_value and their respective success failure responses
#             # it will be seamless
#             # if it can't find it, it will return kbucket of closest nodes.
#
#             if find_value_response == True:
#                 return True
#             else:
#                 return False
#
#     async def handle_put_request(self, reader: StreamReader, writer: StreamWriter, ttl: int, replication: int, key: int,
#                                  value: bytes):
#         """
#         This method handles a put request. The Kademlia network will do its best effort to store the value in the DHT.
#         The local node first locates the closest nodes to the key and then sends them the STORE value instruction.
#         :param reader: The StreamReader of the socket.
#         :param writer: The StreamWriter of the socket.
#         :param ttl: The time to live of the value to be added in the DHT.
#         :param replication: The suggested number of different nodes where the value should be stored.
#         :param key: The key associated to the value
#         :param value: The data to be stored
#         :return: True if the operation was successful.
#         """
#         return_value = self.k_handler.handle_store_request(reader=reader, writer =writer, ttl=ttl,replication=replication,key=key,value=value)
#         return return_value














