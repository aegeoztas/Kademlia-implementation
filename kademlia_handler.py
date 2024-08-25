import asyncio

from LocalNode import LocalNode
from k_bucket import NodeTuple
from util import *
from asyncio.streams import StreamReader, StreamWriter
from Constants import *

class KademliaHandler:
    """
    This class is for handling the requests from the Kademlia network.
    """

    def __init__(self, local_node: LocalNode):
        """
        Constructor
        :param local_node: A LocalNode object used to get access to the routing table and the local storage
        """
        self.local_node: LocalNode = local_node

    async def handle_request(self, buf: bytes, reader: StreamReader, writer: StreamWriter):
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
        |  Node ID        |  4             |  35           |  32           |
        +-----------------+----------------+---------------+---------------+
        |  Body           |  36             | end          | Size - 36     |
        +-----------------+----------------+---------------+---------------+
        """
        # Extracting header, node id and body of the message
        header = buf[:SIZE_FIELD_SIZE + MESSAGE_TYPE_FIELD_SIZE]
        node_id_bytes = buf[SIZE_FIELD_SIZE + MESSAGE_TYPE_FIELD_SIZE: SIZE_FIELD_SIZE +
                                                                       MESSAGE_TYPE_FIELD_SIZE + KEY_SIZE]
        body = buf[SIZE_FIELD_SIZE + MESSAGE_TYPE_FIELD_SIZE + KEY_SIZE:]

        # Extracting the message type
        message_type = struct.unpack(">H", header[2:4])[0]

        return_status = False

        # A specific handler is called depending on the message type.
        try:
            match message_type:

                # Kademlia specific messages
                # TODO add try catch
                case Message.PING:
                    return_status = await self.handle_ping_request(reader, writer, body)
                case Message.STORE:
                    return_status = await self.handle_store_request(reader, writer, body)
                case Message.FIND_NODE:
                    return_status = await self.handle_find_node_request(reader, writer, body)
                case Message.FIND_VALUE:
                    return_status = await self.handle_find_value_request(reader, writer, body)
                case _:
                    await bad_packet(reader, writer,
                                     f"Unknown message type {message_type} received",
                                     header)

        except Exception as e:
            await bad_packet(reader, writer, f"Wrongly formatted message", buf)

        # If the operation was successful we update our routing table with the information of the remote peer.
        if return_status:
            remote_address, remote_port = writer.get_extra_info("socket").getpeername()
            node_id = int.from_bytes(node_id_bytes, "big")

            async with self.local_node.routing_table_lock:
                self.local_node.routing_table.update_table(remote_address, remote_port, node_id)

        return return_status


    async def handle_ping_request(self, reader, writer, request_body: bytes):
        """
        This function handles a ping message. It will just send a pong response.
        :param reader: The reader of the socket.
        :param writer: The writer of the socket.
        :param request_body: The body of the ping message.
        :return: True if the operation was successful.
        """

        """
        Structure of request_body
        +-----------------+----------------+---------------+---------------+
        |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
        +-----------------+----------------+---------------+---------------+
        |  RPC ID         |  0             |  15           |  15           |
        +-----------------+----------------+---------------+---------------+
        """

        if len(request_body) != RPC_ID_FIELD_SIZE:
            raise ValueError("PING body request has invalid size")

        rpc_id : bytes = request_body

        """
        Structure of PING_RESPONSE message
        +-----------------+----------------+---------------+---------------+
        |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
        +-----------------+----------------+---------------+---------------+
        |  Size           |  0             |  1            |  2            |
        +-----------------+----------------+---------------+---------------+
        |  Message type   |  2             |  3            |  2            |
        +-----------------+----------------+---------------+---------------+
        |  RPC ID         |  4             |  19           |  16           |
        +-----------------+----------------+---------------+---------------+
        """
        # Define the ping response message
        message_size = SIZE_FIELD_SIZE + MESSAGE_TYPE_FIELD_SIZE + RPC_ID_FIELD_SIZE
        message_type = Message.PING_RESPONSE

        response = struct.pack(">HH", message_size, message_type) + rpc_id

        # Send the response
        try:
            writer.write(response)
            await writer.drain()

            # Get the address of the remote peer
            remote_address, remote_port = writer.get_extra_info("socket").getpeername()
            print(f"[+] {remote_address}:{remote_port} <<< PING_RESPONSE")
            return True

        except Exception as e:
            print(f"[-] Failed to send PING_RESPONSE {e}")
            await bad_packet(reader, writer)
            return False

    async def handle_store_request(self, reader, writer, request_body: bytes):
        """
        This method handle a store message. If this function is called, this node has been designated to store a value.
        The node must then store the value in its storage.
        :param reader: The reader of the socket.
        :param writer: The writer of the socket.
        :param request_body: The body of the request.
        :return: True if the operation was successful.
        """

        """
        Structure of request body
        +-----------------+----------------+---------------+---------------+
        |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
        +-----------------+----------------+---------------+---------------+
        |  RPC ID         |  0             | 16            | 16            |
        +-----------------+----------------+---------------+---------------+
        |  key            |  17            | 48            |  32           |
        +-----------------+----------------+---------------+---------------+
        |  TTL            |  49            | 51            |  2            |
        +-----------------+----------------+---------------+---------------+
        |  value          |  52            | end           |   variable    |
        +-----------------+----------------+---------------+---------------+
        """

        if len(request_body) < RPC_ID_FIELD_SIZE + KEY_SIZE + TTL_FIELD_SIZE:
            raise ValueError("STORE request body has invalid size")

        # Extracting fields from request
        index=0
        rpc_id : bytes = request_body[index:RPC_ID_FIELD_SIZE]
        index+=RPC_ID_FIELD_SIZE
        key : int = int.from_bytes(request_body[index:index+KEY_SIZE], byteorder='big')
        index+=KEY_SIZE
        ttl: int = int.from_bytes(request_body[index:index+TTL_FIELD_SIZE], byteorder='big')
        index+=TTL_FIELD_SIZE
        value : bytes = request_body[index:]

        # If the ttl is 0, the request is dropped.
        if ttl <=  0:
            return False
        elif ttl > MAX_TTL:
            ttl = MAX_TTL

        # Store the value in the local storage
        async with self.local_node.local_hash_table_lock:
            self.local_node.local_hash_table.put(key, value, ttl)
        return True


    async def handle_find_node_request(self, reader, writer, request_body: bytes):
        """
        This method handle a find_node request. The local node will send back the k known closest known to the key
        present in the message.
        :param reader: The reader of the socket.
        :param writer: The writer of the socket.
        :param request_body: The body of the find_node request.
        :return: True if the operation was successful.
        """

        """
        Structure of request body
        +-----------------+----------------+---------------+---------------+
        |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
        +-----------------+----------------+---------------+---------------+
        |  RPC ID         |  0             | 16            | 16            |
        +-----------------+----------------+---------------+---------------+
        |  key            |  17            | 48            |  32           |
        +-----------------+----------------+---------------+---------------+
        """

        if len(request_body) != RPC_ID_FIELD_SIZE + KEY_SIZE:
            raise ValueError("Find node request body has invalid size")

        rpc_id : bytes = request_body[0:RPC_ID_FIELD_SIZE]
        key : int = int.from_bytes(request_body[RPC_ID_FIELD_SIZE:RPC_ID_FIELD_SIZE+KEY_SIZE], byteorder='big')

        # Getting the closest nodes
        async with self.local_node.routing_table_lock:
            closest_nodes: list[NodeTuple] = self.local_node.routing_table.get_nearest_peers(key, NB_OF_CLOSEST_PEERS)

        nb_of_nodes_found = len(closest_nodes)

        """
        Structure of FIND_NODE_RESP message
        +-----------------+----------------+---------------+---------------+
        |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
        +-----------------+----------------+---------------+---------------+
        |  Size           |  0             |  1            |  2            |
        +-----------------+----------------+---------------+---------------+
        |  Message type   |  2             |  3            |  2            |
        +-----------------+----------------+---------------+---------------+
        |  RPC ID         |  4             |  19           |  16           |
        +-----------------+----------------+---------------+---------------+
        | Nb_node_found   |  20            |  21           |  2            |
        +-----------------+----------------+---------------+---------------+
        | IP 1            |  22             |  -           |  4            |
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

        # Constructing response message

        # Header
        message_size = (SIZE_FIELD_SIZE + MESSAGE_TYPE_FIELD_SIZE+ RPC_ID_FIELD_SIZE + NUMBER_OF_NODES_FIELD_SIZE +
                        (KEY_SIZE + IP_FIELD_SIZE + PORT_FIELD_SIZE) * nb_of_nodes_found)

        response = struct.pack(">HH", message_size, Message.FIND_NODE_RESP)
        response += rpc_id
        response += struct.pack(">H", nb_of_nodes_found)


        # Add each node information to the message

        for node in closest_nodes:
            # Add IP field
            response += socket.inet_aton(node.ip_address)
            # Add port field
            response += struct.pack(">H", node.port)
            # Add node ID field
            response += int.to_bytes(node.node_id, 32, byteorder='big')

        # Send the response
        try:
            writer.write(response)
            await writer.drain()
        except Exception as e:
            print(f"[-] Failed to send FIND_NODE_RESP {e}")
            await bad_packet(reader, writer, data=response)
            return False

        # Get the address of the remote peer
        remote_address, remote_port = writer.get_extra_info("socket").getpeername()

        print(f"[+] {remote_address}:{remote_port} <<< FIND_NODE_RESP")
        return True




    async def handle_find_value_request(self, reader, writer, request_body: bytes)->bool:
        """
        This method handle a find value message. It will either send the value back if it is present in the local
        storage or the known k-closest nodes to the key if it is not
        :param reader: The reader of the socket.
        :param writer: The writer of the socket.
        :param request_body: The body of the request.
        :return: True if the operation was successful.
        """
        """
        Structure of request body
        +-----------------+----------------+---------------+---------------+
        |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
        +-----------------+----------------+---------------+---------------+
        |  RPC ID         |  0             | 16            | 16            |
        +-----------------+----------------+---------------+---------------+
        |  key            |  17            | 48            |  32           |
        +-----------------+----------------+---------------+---------------+
        """
        if len(request_body) != RPC_ID_FIELD_SIZE + KEY_SIZE:
            raise ValueError("Find value request body has invalid size")

        # Extracting fields from request
        index = 0
        rpc_id: bytes = request_body[index:RPC_ID_FIELD_SIZE]
        index += RPC_ID_FIELD_SIZE
        key: int = int.from_bytes(request_body[index:index + KEY_SIZE], byteorder='big')

        # Checking if the value is in the local storage
        async with self.local_node.local_hash_table_lock:
            value : bytes = self.local_node.local_hash_table.get(key)

        # If the value is present, we return it.
        if value:

            """
            Structure of FIND_VALUE_RESP message
            +-----------------+----------------+---------------+---------------+
            |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
            +-----------------+----------------+---------------+---------------+
            |  Size           |  0             |  1            |  2            |
            +-----------------+----------------+---------------+---------------+
            |  Message type   |  2             |  3            |  2            |
            +-----------------+----------------+---------------+---------------+
            |  RPC ID         |  4             |  19           |  16           |
            +-----------------+----------------+---------------+---------------+
            |  value          |  20            |  -            |  -            |
            +-----------------+----------------+---------------+---------------+
            """
            # Constructing response message

            # Header
            message_size = SIZE_FIELD_SIZE + MESSAGE_TYPE_FIELD_SIZE + RPC_ID_FIELD_SIZE + len(value)

            response = struct.pack(">HH", message_size, Message.FIND_VALUE_RESP)
            response += rpc_id
            response += value

            # Send the response
            try:
                writer.write(response)
                await writer.drain()
            except Exception as e:
                print(f"[-] Failed to send FIND_VALUE_RESP {e}")
                await bad_packet(reader, writer, data=response)
                return False

            # Get the address of the remote peer
            remote_address, remote_port = writer.get_extra_info("socket").getpeername()

            print(f"[+] {remote_address}:{remote_port} <<< FIND_VALUE_RESP")
            return True

        else:
            # If the value is not present in the local storage, the list of known closest nodes to the key of the value
            # is returned.
            return await self.handle_find_value_request(reader, writer, request_body)



