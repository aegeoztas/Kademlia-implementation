import asyncio
import concurrent
from LocalNode import LocalNode
from kademlia import NodeTuple
import os
import sys
from dotenv import load_dotenv
from util import *
from asyncio.streams import StreamReader, StreamWriter
from Connection import Connection
from kademlia.distance import key_distance
from MessageTypes import Message
import heapq

load_dotenv()
# Fields sizes in number of bytes
SIZE_FIELD_SIZE = os.getenv("SIZE_FIELD_SIZE")
MESSAGE_TYPE_FIELD_SIZE = os.getenv("MESSAGE_TYPE_FIELD_SIZE")
KEY_SIZE = os.getenv("KEY_SIZE")
IP_FIELD_SIZE = os.getenv("IP_FIELD_SIZE")
PORT_FIELD_SIZE = os.getenv("PORT_FIELD_SIZE")
NB_OF_CLOSEST_PEERS = os.getenv("NB_OF_CLOSEST_PEERS")

# Concurrency parameter
ALPHA = os.getenv("ALPHA")
TIMEOUT = os.getenv("TIMEOUT")
MAXREPLICATION = os.getenv("MAX_REPLICATION")
TLL_SIZE =   os.getenv("TLL_SIZE")
MAXTTL = os.getenv("MAX_TTL")
REPLICATION_SIZE = os.getenv("REPLICATION_SIZE")
# TODO finish dht get
# TODO finish dht put
# TODO implment echo
# TODO (EGE) I feel like we have used the aplha value wrong and made a mistake there go over it later.
"""
"In All RPCs, the recipent must echo a 160 bit random rpc ID which provides some resistance to address forgery. 
PINGS can also be piggy backed on RPC replies for RPC recipient to obtain additional assurance of the sender's network address. 
"""
# TODO add a way for DHThandler (or just handler?) to use kademlia one.




class KademliaHandler:
    """
    This class is for handlig the API calls for the
    Kademlia three
    """

    def __init__(self, local_node: LocalNode):
        """
        Constructor
        :param local_node: A LocalNode object used to get access to the routing table and the local storage
        """
        self.local_node: LocalNode = local_node

    async def handle_message(self, buf: bytes, reader: StreamReader, writer: StreamWriter):
        """
        This function handles incoming requests according to their content.
        :param buf: A buffer of bytes containing the content of the message.
        :param reader: The StreamReader of the socker.
        :param writer: The StreamWriter of the socket.
        :return: True if the operation was successful.
        """

        """
        Message Format
        +-----------------+----------------+---------------+---------------+
        |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
        +-----------------+----------------+---------------+---------------+
        |  Size           |  0             |  1            |  2            |
        +-----------------+----------------+---------------+---------------+
        |  Message type   |  2             |  3            |  2            |
        +-----------------+----------------+---------------+---------------+
        |  Body           |  3             | end           | Size -4       |
        +-----------------+----------------+---------------+---------------+
        """
        # Extracting header and body of the message
        header = buf[:4]
        body = buf[4:]

        # Extracting the message type
        message_type = struct.unpack(">HH", header[2:4])

        return_status = False

        # A specific handler is called depending on the message type.
        try:
            match message_type:
                case Message.FIND_VALUE:
                    """
                    Body of FIND_VALUE
                     +-----------------+----------------+---------------+---------------+
                    |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
                    +-----------------+----------------+---------------+---------------+
                    |  key            |  0             |  31           |  32           |
                    +-----------------+----------------+---------------+---------------+
                    """
                    key = int.from_bytes(body[0: KEY_SIZE - 1], byteorder="big")
                    return_status = await self.handle_find_value_request(reader, writer, key)
                case Message.STORE:


                    """
                            Body of STORE MESSAGE
                            +-----------------+----------------+---------------+---------------+
                            |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
                            +-----------------+----------------+---------------+---------------+
                            |  TTL            |  0             |  1            |  2            |
                            +-----------------+----------------+---------------+---------------+
                            |  replication    |  2             |  2            |  1            |
                            +-----------------+----------------+---------------+---------------+
                            |  reserved       |  3             |  3            |  1            |
                            +-----------------+----------------+---------------+---------------+
                            |  key            |  8             |  39           |  32           |
                            +-----------------+----------------+---------------+---------------+
                            |  value          |  40            |  end          |  variable     |
                            +-----------------+----------------+---------------+---------------+
                    """
                    ttl =  int.from_bytes(body[0: TLL_SIZE - 1], byteorder="big")
                    replication = int.from_bytes(body[TLL_SIZE:  TLL_SIZE +REPLICATION_SIZE - 1], byteorder="big")
                    #reserved = int.from_bytes(body[TLL_SIZE +REPLICATION_SIZE ], byteorder="big")
                    key = int.from_bytes(body[TLL_SIZE +REPLICATION_SIZE + 1  : TLL_SIZE +REPLICATION_SIZE + 1  + KEY_SIZE - 1], byteorder="big")
                    value = body[ TLL_SIZE +REPLICATION_SIZE + 1  + KEY_SIZE :]
                    return_status = await self.handle_store_request(replication=replication, ttl= ttl, key=key, value=value)

                # Kademlia specific messages
                case Message.PING:

                    """
                    Body of DHT_PUT
                    +-----------------+----------------+---------------+---------------+
                    |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
                    +-----------------+----------------+---------------+---------------+
                                                    empty
                    """
                    return_status = await self.handle_ping(reader, writer)

                case Message.FIND_NODE:
                    """
                    Body of FIND_NODE 
                    +-----------------+----------------+---------------+---------------+
                    |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
                    +-----------------+----------------+---------------+---------------+
                    |  key            |  0             |  31           |  32           |
                    +-----------------+----------------+---------------+---------------+
                    """
                    key = int.from_bytes(body[0: KEY_SIZE - 1], byteorder="big")
                    return_status = await self.handle_find_nodes_request(reader, writer, key)

                case Message.STORE:
                    # this is pretty much equal to dht put
                    """
                    Body of DHT_PUT
                    +-----------------+----------------+---------------+---------------+
                    |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
                    +-----------------+----------------+---------------+---------------+
                    |  size           |  0             |  1            |  2            |
                    +-----------------+----------------+---------------+---------------+
                    |  STORE          |  2             |  3            |  2            |
                    +-----------------+----------------+---------------+---------------+
                    |  DHT_PUT        |  4             |  5            |  2            |
                    +-----------------+----------------+---------------+---------------+
                    |  replication    |  6             |  6            |  1            |
                    +-----------------+----------------+---------------+---------------+
                    |  reserved       |  7             |  7            |  1            |
                    +-----------------+----------------+---------------+---------------+
                    |  key            |  8             |  39           |  32           |
                    +-----------------+----------------+---------------+---------------+
                    |  value          |  40            |  end          |  variable     |
                    +-----------------+----------------+---------------+---------------+
                    """
                    ttl = body[0]
                    key = int.from_bytes(struct.unpack(f">{KEY_SIZE}s", body[1: 1 + KEY_SIZE - 1]),
                                         byteorder="big")
                    value_field_size = len(body) - KEY_SIZE - 1
                    value = struct.unpack(f">{value_field_size}s", body[KEY_SIZE + 1:])
                    return_status = await self.handle_store_request(ttl, key, value)

                case _:
                    await bad_packet(reader, writer,
                                     f"Unknown message type {message_type} received",
                                     header)

        except Exception as e:
            await bad_packet(reader, writer, f"Wrongly formatted message", buf)
        return return_status
    async def handle_ping(self, reader, writer):
        """
        This function handles a ping message. It will just send a pong response.
        :param reader: The reader of the socket.
        :param writer: The writer of the socket.
        :return: True if the operation was successful.
        """
        # Get the address of the remote peer
        remote_address, remote_port = writer.get_extra_info("socket").getpeername()
        # Define the ping response message
        message_size = int(SIZE_FIELD_SIZE + MESSAGE_TYPE_FIELD_SIZE)
        response = struct.pack(">HH", message_size, 0)
        # here I sent a 0 type message for the ping response.
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
    async def republish_store_request(self, replication: int, ttl: int, key: int, value: bytes):
        """
        this function gets the leftovers from handle_store_function and
        tries to replicate the storage evenly as possible.
        """

        # TODO add key mixing to this function so each repub has a different key for the same value
        # then on our local bucket send closest places
        nodes_to_store: list[NodeTuple] = self.local_node.routing_table.get_nearest_peers(key, NB_OF_CLOSEST_PEERS)
        # both depth wise(how many hops to last) AND width wise (how many paralel hops).
        # also replication might also be used to tell how many times same key should be used.
        # like maybe use different keys

        tasks = []
        if nodes_to_store:
            # Calculate how much each node should replicate.
            base_rep = replication // len(nodes_to_store)  # use floor division 8 // 3 = 2
            extra = replication % len(nodes_to_store)  # 8 % 3 = 2
            # so for 8 repetition among 3 nodes we would add +1 to first 2 nodes

            # Generate tasks for sending store messages.
            tasks = []
            for i, node in enumerate(nodes_to_store):
                # Distribute the 'extra' replications across the first 'extra' nodes.
                if i < extra:
                    rep_to_send = base_rep + 1
                else:
                    rep_to_send = base_rep

                tasks.append(self.send_store_message(node, rep_to_send, ttl, key, value))
    async def handle_store_request(self, replication: int, ttl: int, key: int, value: bytes):
        """
        This function handles a store message. If this function is called, this node has been designated to store a value.
        It must then store the value in its storage.
        :param reader: The reader of the socket.
        :param replication: the number of times that this key,value pair should be replicated through the network.
        :param ttl: The time to live of the value to be stored.
        :param key: The 256 bit key associated to the value.
        :param value: The value to be stored.
        :return: True if the operation was successful.
        """
        if ttl == 0:
            # it is forbiden to have 0 ttl so we drop the request
            return False
        elif ttl> MAXTTL:
            ttl = MAXTTL

        self.local_node.local_hash_table.put(key, value, ttl)

        if replication == 0:
            return True
        elif replication > MAXREPLICATION:
            replication = MAXREPLICATION
            #here the replication is only a hint and too much of it can be bad.
            # so we set cap on it.
        self.republish_store_request(replication,ttl,key,value)

    async def handle_find_value_request(self, reader, writer, key: int):
        """
        This function finds if it has the key asked.
        if not returns to the sender the k closest nodes to the key,that is located in its routing table.
        :param key:The key for which we want to find.
        :param reader: The reader of the socket
        :param writer: The writer of the socket
        :return: True if the operation was successful.
        """
        value = self.local_node.local_hash_table.get(key)
        if value != None:
            # if value is existing send it back
            message_size = int(SIZE_FIELD_SIZE
                           + MESSAGE_TYPE_FIELD_SIZE
                           + sys.getsizeof(value) )
            header = struct.pack(">HH", message_size, Message.FIND_VALUE_SUCCESS)
            if type(value) == bytes:
                body = value
            else:
                body = value.to_bytes(KEY_SIZE, byteorder="big")
            response = header + body
            try:
                writer.write(response)
                await writer.drain()
            except Exception as e:
                print(f"[-] Failed to send FIND_VALUE_SUCCESS {e}")
                await bad_packet(reader, writer, data=response)
                return False
        else:
            # else this acts as handle_find_nodes_request
            return self.handle_find_nodes_request(reader,writer,key)

    async def handle_find_nodes_request(self, reader, writer, key: int):
        """
        This function returns to the sender the k closest nodes to a key located in its routing table.
        :param key:The key for which we want to find the closest nodes to this key.
        :param reader: The reader of the socket
        :param writer: The writer of the socket
        :return: True if the operation was successful.
        """

        # Get the address of the remote peer
        remote_address, remote_port = writer.get_extra_info("socket").getpeername()

        # Getting the closest nodes
        closest_nodes: list[NodeTuple] = self.local_node.routing_table.get_nearest_peers(key, NB_OF_CLOSEST_PEERS)
        nb_of_nodes_found = len(closest_nodes)

        NUMBER_OF_NODES_FIELD_SIZE = 2

        # Constructing response message
        message_size = int(SIZE_FIELD_SIZE
                           + MESSAGE_TYPE_FIELD_SIZE
                           + NUMBER_OF_NODES_FIELD_SIZE
                           + (KEY_SIZE + IP_FIELD_SIZE + PORT_FIELD_SIZE) * nb_of_nodes_found)
        response = struct.pack(">HHH", message_size, Message.FIND_NODE_RESP, nb_of_nodes_found)

        # Add each node information to the message
        """
        
               Body of FIND_NODE_RESPONSE
               +-----------------+----------------+---------------+---------------+
               |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
               +-----------------+----------------+---------------+---------------+
               |  node_id        |  0             |  31           |  32           |
               +-----------------+----------------+---------------+---------------+
               |  IP_field1      |  32            |  32           |  1           |
               +-----------------+----------------+---------------+---------------+
               |  IP_field2      |  33            |  33           |  1           |
               +-----------------+----------------+---------------+---------------+
               |  IP_field3      |  34            |  34           |  1           |
               +-----------------+----------------+---------------+---------------+
               |  IP_field4      |  35            |  35           |  1           |
               +-----------------+----------------+---------------+---------------+
               |  Node Port      |  36            |  37           |  2           |
               +-----------------+----------------+---------------+---------------+
        
        """
        for node in closest_nodes:
            # Add node ID field
            response += struct.pack("B" * KEY_SIZE, node.node_id)
            # Add IP field
            ip_parts = map(int, node.ip_address.split())
            response += struct.pack(">BBBB", *ip_parts)
            # Add port field
            response += struct.pack(">H", node.port)

        # Send the response
        try:
            writer.write(response)
            await writer.drain()
        except Exception as e:
            print(f"[-] Failed to send DHT_FIND_NODE_RESP {e}")
            await bad_packet(reader, writer, data=response)
            return False
        print(f"[+] {remote_address}:{remote_port} <<< DHT_SUCCESS")
        return True

    async def find_closest_nodes_in_network(self, key: int):
        """
               kademlia algorithms find node process.
               Uses send_find_closest_nodes_message to ittarate through the network.
               takes a node id and recipient of the message instead of a
               single Node tuple returns the k-nodes it knows that are closest to the given node id.
               """
        """ 
               Body of FIND_NODE 
               +-----------------+----------------+---------------+---------------+
               |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
               +-----------------+----------------+---------------+---------------+
               |  key            |  0             |  31           |  32           |
               +-----------------+----------------+---------------+---------------+
        """
        class ComparableNodeTuple:
            # this is a class to handle node comparisons based on their distance to the key
            def __init__(self, nodeTuple: NodeTuple, reference_key: int):
                self.nodeTuple : NodeTuple = nodeTuple
                self.reference_key : int = reference_key
            def __lt__(self, other):
                # The minimum of the heap will be the node with the greatest distance
                return key_distance(self.nodeTuple.node_id, self.reference_key) > key_distance(other.nodeTuple.node_id, self.reference_key)

        nodes_to_query: list[NodeTuple] = self.local_node.routing_table.get_nearest_peers(key, NB_OF_CLOSEST_PEERS)
        closest_nodes : list[ComparableNodeTuple] = [ComparableNodeTuple(node, key) for node in nodes_to_query]
        heapq.heapify(closest_nodes)

        contacted_nodes: set[NodeTuple] = set()
        # send our closest nodes find node message.
        tasks = [self.send_find_closest_nodes_message(node, key) for node in nodes_to_query]

        while tasks:
            done_tasks, pending_tasks = asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

            for completed_task in done_tasks:
                k_closest_nodes_received = await completed_task
                if k_closest_nodes_received is not None:
                    for node in k_closest_nodes_received:
                        comparable_node = ComparableNodeTuple(node, key)
                        if node not in contacted_nodes:
                            contacted_nodes.add(node)  # add the node to contacted nodes.
                            # If the new node is closer than the furthest in the heap, add it
                            if comparable_node < closest_nodes[0]:
                                heapq.heappushpop(closest_nodes, comparable_node)
                                tasks.append(asyncio.create_task(self.send_find_closest_nodes_message(node, key)))

        # cleanup any and all tasks
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        # return k closest nodes
        return [node.nodeTuple for node in heapq.nsmallest(NB_OF_CLOSEST_PEERS, closest_nodes)]
    async def send_find_value_message(self, recipient: NodeTuple,value: bytes):
        """
        sends FIND_VALUE message of the Kademlia.
        This method is responsible for sending a find value message.
        SIMILAR TO DHT_GET message.
        :param key: The key used to find the closest nodes.
        :param recipient: A node tuple that represents the peer to which the message will be sent.
        :return: True if the operation was successful.
        """


        """
        Structure of FIND_NODE query
        +-----------------+----------------+---------------+---------------+
        |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
        +-----------------+----------------+---------------+---------------+
        |  size           |  0             |  1            |  2            |
        +-----------------+----------------+---------------+---------------+
        |  FIND_VALUE     |  2             |  3            |  2            |
        +-----------------+----------------+---------------+---------------+
        |  key            |  4             |  259          |  256          |
        +-----------------+----------------+---------------+---------------+
        """

        message_size = SIZE_FIELD_SIZE + MESSAGE_TYPE_FIELD_SIZE + KEY_SIZE
        header = struct.pack(">HH", message_size, Message.FIND_NODE)
        body = value
        query = header+body
        # Make the connection to the remote peer
        ip: str = recipient.ip_address
        port: int = recipient.port
        connection: Connection = Connection(ip, port, TIMEOUT)
        if await connection.connect() and await connection.send_message(query):
            message_type_response, body_response = await connection.receive_message()
        else:
            await connection.close()
            return False
        # Verify that the response has the correct format.
        if message_type_response is None or body_response is None or message_type_response != Message.FIND_NODE_RESP:
            print("Failed to get DHT_FIND_NODE_RESP")
            await connection.close()
            return False
        else:
            # We first close the socket
            await connection.close()
            """
            Structure of DHT_FIND_NODE_RESP body message
            +-----------------+----------------+---------------+---------------+
            |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
            +-----------------+----------------+---------------+---------------+
            |  nb_of_nodes    |  0             |  1            |  2            |
            +-----------------+----------------+---------------+---------------+
            |  key_node_1     |  2             |  33           |  32           |
            +-----------------+----------------+---------------+---------------+
            |  ip_node_1      |  34            |  37           |  4            |
            +-----------------+----------------+---------------+---------------+
            |  port_node_1    |  38            |  40           |  2            |
            +-----------------+----------------+---------------+---------------+
            ...
            |  key_node_n     |  ...           |  ...          |  32           |
            +-----------------+----------------+---------------+---------------+
            |  ip_node_n      |  ...           |  ...          |  4            |
            +-----------------+----------------+---------------+---------------+
            |  port_node_n    |  ...           |  ...          |  2            |
            +-----------------+----------------+---------------+---------------+
            """
            # Extracting the fields of the message
            try:
                list_of_returned_nodes: list[NodeTuple] = list()
                nb_of_nodes: int = struct.unpack(">H", body_response[0:3])
                read_head = 3
                for i in range(nb_of_nodes):
                    key_node: int = int.from_bytes(body_response[read_head:read_head + KEY_SIZE - 1], byteorder="big")
                    read_head += KEY_SIZE
                    ip_node: str = socket.inet_ntoa(body_response[read_head:read_head + IP_FIELD_SIZE - 1])
                    read_head += IP_FIELD_SIZE
                    port_node: int = struct.unpack(">H", body_response[read_head:read_head + PORT_FIELD_SIZE - 1])
                    read_head += PORT_FIELD_SIZE
                    received_node = NodeTuple(ip_node, port_node, key_node)
                    list_of_returned_nodes[i] = received_node

                return list_of_returned_nodes

            except Exception as e:
                print("Body of the response has the wrong format")
                return None
    async def send_find_closest_nodes_message(self, recipient: NodeTuple, key: int) -> list[NodeTuple]:
        """
        FIND_NODES message of the Kademlia.
        This method is responsible for sending a find node message.
        :param key: The key used to find the closest nodes.
        :param recipient: A node tuple that represents the peer to which the message will be sent.
        :return: True if the operation was successful.
        """
        # Definition of FIND_NODES query
        """
        Structure of FIND_NODES query
        +-----------------+----------------+---------------+---------------+
        |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
        +-----------------+----------------+---------------+---------------+
        |  size           |  0             |  1            |  2            |
        +-----------------+----------------+---------------+---------------+
        |  FIND_NODES     |  2             |  3            |  2            |
        +-----------------+----------------+---------------+---------------+
        |  key            |  4             |  259          |  256          |
        +-----------------+----------------+---------------+---------------+
        """
        message_size = SIZE_FIELD_SIZE + MESSAGE_TYPE_FIELD_SIZE + KEY_SIZE
        query = struct.pack(">HH", message_size, Message.FIND_NODE)
        query += key.to_bytes(KEY_SIZE, byteorder="big")

        # Make the connection to the remote peer
        ip: str = recipient.ip_address
        port: int = recipient.port
        connection: Connection = Connection(ip, port, TIMEOUT)
        if await connection.connect() and await connection.send_message(query):
            message_type_response, body_response = await connection.receive_message()
        else:
            await connection.close()
            return False
        # Verify that the response has the correct format.
        if message_type_response is None or body_response is None or message_type_response != Message.FIND_NODE_RESP:
            print("Failed to get DHT_FIND_NODE_RESP")
            await connection.close()
            return False
        else:
            # We first close the socket
            await connection.close()
            """
            Structure of DHT_FIND_NODE_RESP body message
            +-----------------+----------------+---------------+---------------+
            |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
            +-----------------+----------------+---------------+---------------+
            |  nb_of_nodes    |  0             |  1            |  2            |
            +-----------------+----------------+---------------+---------------+
            |  key_node_1     |  2             |  33           |  32           |
            +-----------------+----------------+---------------+---------------+
            |  ip_node_1      |  34            |  37           |  4            |
            +-----------------+----------------+---------------+---------------+
            |  port_node_1    |  38            |  40           |  2            |
            +-----------------+----------------+---------------+---------------+
            ...
            |  key_node_n     |  ...           |  ...          |  32           |
            +-----------------+----------------+---------------+---------------+
            |  ip_node_n      |  ...           |  ...          |  4            |
            +-----------------+----------------+---------------+---------------+
            |  port_node_n    |  ...           |  ...          |  2            |
            +-----------------+----------------+---------------+---------------+
            """
            # Extracting the fields of the message
            try:
                list_of_returned_nodes : list[NodeTuple] = list()
                nb_of_nodes: int = struct.unpack(">H", body_response[0:3])
                read_head = 3
                for i in range(nb_of_nodes):
                    key_node: int = int.from_bytes(body_response[read_head:read_head+KEY_SIZE-1], byteorder="big")
                    read_head += KEY_SIZE
                    ip_node: str = socket.inet_ntoa(body_response[read_head:read_head + IP_FIELD_SIZE-1])
                    read_head += IP_FIELD_SIZE
                    port_node: int = struct.unpack(">H", body_response[read_head:read_head+PORT_FIELD_SIZE-1])
                    read_head += PORT_FIELD_SIZE
                    received_node = NodeTuple(ip_node, port_node, key_node)
                    list_of_returned_nodes[i] = received_node

                return list_of_returned_nodes

            except Exception as e:
                print("Body of the response has the wrong format")
                return None

    async def send_store_message(self,recipient: NodeTuple, replication: int, ttl: int, key: int, value: bytes):


        """
               sends STORE message of the Kademlia.
               This method is responsible for sending a find value message.
               SIMILAR TO DHT_PUT message.
               :param key: The key used to find the closest nodes.
               :param recipient: A node tuple that represents the peer to which the message will be sent.
               :return: True if the operation was successful.
               """

        """
        Structure of STORE MESSAGE
        +-----------------+----------------+---------------+---------------+
        |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
        +-----------------+----------------+---------------+---------------+
        |  size           |  0             |  1            |  2            |
        +-----------------+----------------+---------------+---------------+
        |  STORE          |  2             |  3            |  2            |
        +-----------------+----------------+---------------+---------------+
        |  TTL            |  4             |  5            |  2            |
        +-----------------+----------------+---------------+---------------+
        |  replication    |  6             |  6            |  1            |
        +-----------------+----------------+---------------+---------------+
        |  reserved       |  7             |  7            |  1            |
        +-----------------+----------------+---------------+---------------+
        |  key            |  8             |  39           |  32           |
        +-----------------+----------------+---------------+---------------+
        |  value          |  40            |  end          |  variable     |
        +-----------------+----------------+---------------+---------------+
        """

        message_size = (SIZE_FIELD_SIZE
                        + MESSAGE_TYPE_FIELD_SIZE
                        + TLL_SIZE
                        + REPLICATION_SIZE
                        + 1
                        + KEY_SIZE)
        header = struct.pack(">HH", message_size, Message.FIND_NODE)
        body = key.to_bytes(KEY_SIZE, byteorder="big")
        body += value
        query = header + body
        # Make the connection to the remote peer
        ip: str = recipient.ip_address
        port: int = recipient.port
        connection: Connection = Connection(ip, port, TIMEOUT)
        await connection.connect()
        await connection.send_message(query)
        # there is no need to verify response to a store message
        await connection.close()


class DHTHandler:
    """
    The role of this class is to handle incoming messages that are
    reaching the local node and using DHT API
    """

    def __init__(self, local_node: LocalNode, kademlia_handler: KademliaHandler):
        self.local_node: LocalNode = local_node
        self.k_handler = kademlia_handler
        """

        Constructor
        :param local_node: A LocalNode object used to get access to the routing table and the local storage

        """

    async def handle_message(self, buf: bytes, reader: StreamReader, writer: StreamWriter):
        """
        This function handles incoming requests according to their content.
        :param buf: A buffer of bytes containing the content of the message.
        :param reader: The StreamReader of the socker.
        :param writer: The StreamWriter of the socket.
        :return: True if the operation was successful.
        """

        """
        Message Format
        +-----------------+----------------+---------------+---------------+
        |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
        +-----------------+----------------+---------------+---------------+
        |  Size           |  0             |  1            |  2            |
        +-----------------+----------------+---------------+---------------+
        |  Message type   |  2             |  3            |  2            |
        +-----------------+----------------+---------------+---------------+
        |  Body           |  3             | end           | Size -4       |
        +-----------------+----------------+---------------+---------------+
        """
        # Extracting header and body of the message
        header = buf[:4]
        body = buf[4:]

        # Extracting the message type
        message_type = struct.unpack(">HH", header[2:4])

        return_status = False

        # A specific handler is called depending on the message type.
        try:
            match message_type:
                # DHT API Messages
                case Message.DHT_GET:
                    """
                    Body of DHT_GET
                    +-----------------+----------------+---------------+---------------+
                    |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
                    +-----------------+----------------+---------------+---------------+
                    |  key            |  0             |  31           |  32           |
                    +-----------------+----------------+---------------+---------------+
                    """
                    key = int.from_bytes(body[0: KEY_SIZE - 1])
                    return_status = await self.handle_get_request(reader, writer, key)

                case Message.DHT_PUT:
                    """
                    Body of DHT_PUT
                    +-----------------+----------------+---------------+---------------+
                    |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
                    +-----------------+----------------+---------------+---------------+
                    |  ttl            |  0             |  1            |  2            |
                    +-----------------+----------------+---------------+---------------+
                    |  replication    |  2             |  2            |  1            |
                    +-----------------+----------------+---------------+---------------+
                    |  reserved       |  3             |  3            |  1            |
                    +-----------------+----------------+---------------+---------------+
                    |  key            |  4             |  35           |  32           |
                    +-----------------+----------------+---------------+---------------+
                    |  value          |  36            |  end          |  variable     |
                    +-----------------+----------------+---------------+---------------+
                    """
                    ttl: int = int.from_bytes(struct.pack(">H", body[0:2]))
                    replication: int = body[2]
                    key: int = int.from_bytes(body[4:4 + KEY_SIZE - 1], byteorder="big")
                    value: bytes = body[260:]
                    return_status = await self.handle_put_request(reader, writer, ttl, replication, key, value)

                case _:
                    await bad_packet(reader, writer,
                                     f"Unknown message type {message_type} received",
                                     header)

        except Exception as e:
            await bad_packet(reader, writer, f"Wrongly formatted message", buf)
        return return_status

    async def handle_get_request(self, reader, writer, key: int):
        """
        This method handles a get message. If the local node contains the data,
        it will simply return it. If not, it will try to get from the kademlia network.
        if it cant find it returns DHT_Success or DHT_failiure
        :param reader: The reader of the socket.
        :param writer: The writer of the socket.
        :param key: The key associated to the data.
        :return: True if the operation was successful.
        """
        # Get the address of the remote peer
        remote_address, remote_port = writer.get_extra_info("socket").getpeername()

        # Check if the value is in the local storage
        value = self.local_node.local_hash_table.get(key)

        # If the value is not in the local storage, we have to get it from the Kademlia network from the other peers.
        if value is None:
            # TODO retrieve value in the network
            # needs to send a kademlia get message.
            # better to start working there

            value = None
            pass

        # If the value was not found in the network, a DHT_FAILURE will be sent back to the requester.
        if value is None:

            # Define the DHT_FAILURE message
            """
            Structure of DHT_FAILURE  message
            +-----------------+----------------+---------------+---------------+
            |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
            +-----------------+----------------+---------------+---------------+
            |  size           |  0             |  1            |  2            |
            +-----------------+----------------+---------------+---------------+
            |  DHT_FAILURE    |  2             |  3            |  2            |
            +-----------------+----------------+---------------+---------------+
            |  key            |  4             |  35           |  32           |
            +-----------------+----------------+---------------+---------------+
            """
            message_size = SIZE_FIELD_SIZE + MESSAGE_TYPE_FIELD_SIZE + KEY_SIZE
            response = struct.pack(">HH", message_size, Message.DHT_FAILURE)
            response += key.to_bytes(KEY_SIZE, byteorder="big")

            try:
                writer.write(response)
                await writer.drain()
            except Exception as e:
                print(f"[-] Failed to send DHT_FAILURE {e}")
                await bad_packet(reader, writer, data=response)
                return False

            print(f"[+] {remote_address}:{remote_port} <<< DHT_FAILURE")
            return True

        # If the value was found, the value is sent back to the requester
        else:
            # Define the DHT Success message
            """
            Structure of DHT_SUCCESS message
            +-----------------+----------------+---------------+---------------+
            |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
            +-----------------+----------------+---------------+---------------+
            |  size           |  0             |  1            |  2            |
            +-----------------+----------------+---------------+---------------+
            |  DHT_SUCCESS    |  2             |  3            |  2            |
            +-----------------+----------------+---------------+---------------+
            |  key            |  4             |  35           |  32           |
            +-----------------+----------------+---------------+---------------+
            |  value          |  36            |  end          |  variable     |
            +-----------------+----------------+---------------+---------------+
            """

            message_size = SIZE_FIELD_SIZE + MESSAGE_TYPE_FIELD_SIZE + KEY_SIZE + len(value)

            response = struct.pack(">HH", message_size, Message.DHT_SUCCESS)
            response += key.to_bytes(KEY_SIZE, byteorder="big")
            response += value

            try:
                writer.write(response)
                await writer.drain()
            except Exception as e:
                print(f"[-] Failed to send DHT_SUCCESS {e}")
                await bad_packet(reader, writer, data=response)
                return False

            print(f"[+] {remote_address}:{remote_port} <<< DHT_SUCCESS")
            return True

    async def handle_put_request(self, reader: StreamReader, writer: StreamWriter, ttl: int, replication: int, key: int,
                                 value: bytes):
        """
        This method handles a put request. The Kademlia network will do its best effort to store the value in the DHT.
        The local node first locates the closest nodes to the key and then sends them the STORE value instruction.
        :param reader: The StreamReader of the socket.
        :param writer: The StreamWriter of the socket.
        :param ttl: The time to live of the value to be added in the DHT.
        :param replication: The suggested number of different nodes where the value should be stored.
        :param key: The key associated to the value
        :param value: The data to be stored
        :return: True if the operation was successful.
        """
        raise NotImplementedError

