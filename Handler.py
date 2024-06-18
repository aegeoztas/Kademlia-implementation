import concurrent
from LocalNode import LocalNode
from kademlia import NodeTuple
from network.messages import *
from util import *
from asyncio.streams import StreamReader, StreamWriter

# Fields sizes in number of bytes
SIZE_FIELD_SIZE = 2
MESSAGE_TYPE_FIELD_SIZE = 2
KEY_SIZE = 256 / 8
IP_FIELD_SIZE = 32 / 8
PORT_FIELD_SIZE = 16 / 8

NB_OF_CLOSEST_PEERS = 4

# Concurrency parameter
ALPHA = 3


class Handler:
    """
    The role of this class is to handle all incoming messages reaching the local node
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
                # DHT API Messages
                case DHT_GET.value:
                    """
                    Body of DHT_GET
                    +-----------------+----------------+---------------+---------------+
                    |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
                    +-----------------+----------------+---------------+---------------+
                    |  key            |  0             |  255          |  256          |
                    +-----------------+----------------+---------------+---------------+
                    """
                    key = int.from_bytes(struct.unpack(f"", body[0: KEY_SIZE - 1]))
                    return_status = await self.handle_get_request(reader, writer, key)

                case DHT_PUT.value:
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
                    |  key            |  4             |  259          |  256          |
                    +-----------------+----------------+---------------+---------------+
                    |  value          |  260           |  end          |  variable     |
                    +-----------------+----------------+---------------+---------------+
                    """
                    ttl: int = int.from_bytes(struct.pack(">H", body[0:2]))
                    replication: int = body[2]
                    key: int = int.from_bytes(body[4:4 + KEY_SIZE - 1], byteorder="big")
                    value: bytes = body[260:]
                    return_status = await self.handle_put_request(reader, writer, ttl, replication, key, value)

                # Kademlia specific messages
                case DHT_PING.value:
                    """
                    Body of DHT_PUT
                    +-----------------+----------------+---------------+---------------+
                    |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
                    +-----------------+----------------+---------------+---------------+
                                                    empty
                    """
                    return_status = await self.handle_ping(reader, writer)

                case DHT_FIND_NODE.value:
                    """
                    Body of DHT_FIND_NODE 
                    +-----------------+----------------+---------------+---------------+
                    |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
                    +-----------------+----------------+---------------+---------------+
                    |  key            |  0             |  255          |  256          |
                    +-----------------+----------------+---------------+---------------+
                    """
                    key = int.from_bytes(struct.unpack(f">{KEY_SIZE}s", body[0: KEY_SIZE - 1]),
                                         byteorder="big")
                    return_status = await self.handle_find_nodes_request(reader, writer, key)

                case DHT_STORE.value:
                    """
                    Body of DHT_PUT
                    +-----------------+----------------+---------------+---------------+
                    |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
                    +-----------------+----------------+---------------+---------------+
                    |  ttl            |  0             |  0            |  1            |
                    +-----------------+----------------+---------------+---------------+
                    |  key            |  1             |  256          |  256          |
                    +-----------------+----------------+---------------+---------------+
                    |  value          |  257           |  end          |  variable     |
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

    async def handle_get_request(self, reader, writer, key: int):
        """
        This method handles a get message. If the local node contains the data,
        it will simply return it. If not, it will try to get from the network.
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
            |  key            |  4             |  259          |  256          |
            +-----------------+----------------+---------------+---------------+
            """
            message_size = SIZE_FIELD_SIZE + MESSAGE_TYPE_FIELD_SIZE + KEY_SIZE
            response = struct.pack(">HH", message_size, DHT_FAILURE)
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
            |  key            |  4             |  259          |  256          |
            +-----------------+----------------+---------------+---------------+
            |  value          |  260           |  end          |  variable     |
            +-----------------+----------------+---------------+---------------+
            """

            message_size = SIZE_FIELD_SIZE + MESSAGE_TYPE_FIELD_SIZE + KEY_SIZE + len(value)

            response = struct.pack(">HH", message_size, DHT_SUCCESS)
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
        response = struct.pack(">HH", message_size, DHT_PING_RESP)
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

    async def handle_store_request(self, ttl: int, key: int, value: bytes):
        """
        This function handles a store message. If this function is called, this node has been designated to store a value.
        It must then store the value in its storage.
        :param reader: The reader of the socket.
        :param writer: The writer of the socket.
        :param ttl: The time to live of the value to be stored.
        :param key: The 256 bit key associated to the value.
        :param value: The value to be stored.
        :return: True if the operation was successful.
        """
        self.local_node.local_hash_table.put(key, value, ttl)
        return True

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
        response = struct.pack(">HHH", message_size, DHT_FIND_NODE_RESP, nb_of_nodes_found)

        # Add each node information to the message
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

    async def handle_put_request(self):
        return

    #---------------------------------------------------------------------------------------------------------
    # Async functions that are not handler of received messages:
    #---------------------------------------------------------------------------------------------------------

    async def find_closest_nodes_in_network(self, key: int):

        # Definition of query message
        message_size = SIZE_FIELD_SIZE + MESSAGE_TYPE_FIELD_SIZE + KEY_SIZE
        query = struct.pack(">HH", message_size, DHT_FIND_NODE)
        query += struct.pack(">", key)

        nodes_to_query: list[NodeTuple] = self.local_node.routing_table.get_nearest_peers(key, NB_OF_CLOSEST_PEERS)
        contacted_nodes: set[NodeTuple] = set()
        closest_nodes: list[NodeTuple] = list(nodes_to_query)

        current_batch: list[NodeTuple] = list()
        counter = 0
        while counter < ALPHA and len(nodes_to_query) > 0:
            current_batch[counter] = nodes_to_query.pop(0)
            counter += 1

        # Function to handle responses
        def handle_response(future):
            response = future.result()
            print(response)

        # Create a ThreadPoolExecutor to send messages in parallel
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit tasks to the executor
            futures = [executor.submit(send_message, msg) for msg in messages]

            # Attach a callback to each future to handle the response
            for future in futures:
                future.add_done_callback(handle_response)

        # Note: The ThreadPoolExecutor context will wait for all futures to complete before exiting.

        # for every nodes:
        # send
        done = False
        # done = list to query is empty
        # add to list to query only when nodes getted are closer that to node quried
        while not done:
            pass
        for node in nodes_to_query:
            # query node
            # make connection
            # do it parallel and asynchronously


            # list = result
            # TODO add filter to then sending message as well ?
            # filter_result : keep only nodes that are closer than the node itself
            pass

    async def send_find_closest_nodes_message(self, recipient: NodeTuple):
        """

        :param recipient:
        :return:
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
