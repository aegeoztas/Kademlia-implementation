import struct
from Constants import *
from kademlia_service import KademliaService
from asyncio import StreamReader, StreamWriter
from LocalNode import LocalNode
from bad_packet import bad_packet


class DHTHandler:
    """
    The role of this class is to handle incoming messages that are
    reaching the local node and using DHT API
    """

    def __init__(self, local_node: LocalNode, kademlia_service: KademliaService):
        self.local_node = local_node
        self.kademlia_service = kademlia_service


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
        # Extracting fields
        index = 0
        size: int = int.from_bytes(buf[index:index+SIZE_FIELD_SIZE], byteorder='big')
        index += SIZE_FIELD_SIZE
        message_type: int = int.from_bytes(buf[index:index+MESSAGE_TYPE_FIELD_SIZE], byteorder='big')
        index += MESSAGE_TYPE_FIELD_SIZE
        body: bytes = buf[index:]

        return_status = False

        # A specific handler is called depending on the message type.
        try:
            match message_type:

                # DHT API Messages

                # TODO add try catch
                case Message.DHT_GET:
                    return_status = await self.handle_get_request(reader, writer, body)
                case Message.DHT_PUT:
                    return_status = await self.handle_put_request(reader, writer, body)
                case _:
                    await bad_packet(reader, writer,
                                     f"Unknown message type {message_type} received",
                                     buf)
        except Exception as e:
            await bad_packet(reader, writer, f"Wrongly formatted message", buf)

        return return_status

    async def handle_get_request(self, reader, writer, body: bytes)-> bool:
        """
        This method handles a get message. If the local node contains the data,
        it will simply return it. If not, it will try to get it from the kademlia network.
        The method will send either DHT_SUCCESS or DHT_FAILURE.
        :param reader: The reader of the socket.
        :param writer: The writer of the socket.
        :param body: The body of the request.
        :return: True if the operation was successful
        """

        """
        Body of DHT_GET
        +-----------------+----------------+---------------+---------------+
        |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
        +-----------------+----------------+---------------+---------------+
        |  key            |  0             |  31           |  32           |
        +-----------------+----------------+---------------+---------------+
        """

        # Extracting the key
        if len(body) < KEY_SIZE:
            raise ValueError("DHT_GET has invalid body")

        raw_key: bytes = body[:KEY_SIZE]
        key : int = int.from_bytes(raw_key, byteorder='big')

        # We try to get the value from the local storage.
        value: bytes = self.local_node.local_hash_table.get(key)

        # If the value is not found in the local storage, we try to find it in the distributed hash table in the
        # network.
        if not value:
            value = await self.kademlia_service.find_value_in_network(key)

        # If the value is not found, we send DHT_FAILURE
        if not value:
            """
            Structure of DHT_FAILURE response
            +-----------------+----------------+---------------+---------------+
            |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
            +-----------------+----------------+---------------+---------------+
            |  Size           |  0             |  1            |  2            |
            +-----------------+----------------+---------------+---------------+
            |  Message type   |  2             |  3            |  2            |
            +-----------------+----------------+---------------+---------------+
            |  key            |  4             |  35           |  32           |
            +-----------------+----------------+---------------+---------------+
            """

            # Creation of the DHT_FAILURE message
            size: int = SIZE_FIELD_SIZE + MESSAGE_TYPE_FIELD_SIZE + KEY_SIZE
            message_type: int= Message.DHT_FAILURE

            response : bytes = struct.pack(">HH", size, message_type) + raw_key

            # Sending the response
            try:
                writer.write(response)
                await writer.drain()

                # Get the address of the remote peer
                remote_address, remote_port = writer.get_extra_info("socket").getpeername()
                print(f"[+] {remote_address}:{remote_port} <<< DHT_FAILURE")
                return True

            except Exception as e:
                print(f"[-] Failed to send DHT_FAILURE {e}")
                await bad_packet(reader, writer)
                return False

        # If the value is found we send DHT_SUCCESS with the value.
        """
        Structure of DHT_SUCCESS response
        +-----------------+----------------+---------------+---------------+
        |  Field Name     |  Start Byte    |  End Byte     |  Size (Bytes) |
        +-----------------+----------------+---------------+---------------+
        |  Size           |  0             |  1            |  2            |
        +-----------------+----------------+---------------+---------------+
        |  Message type   |  2             |  3            |  2            |
        +-----------------+----------------+---------------+---------------+
        |  key            |  4             |  35           |  32           |
        +-----------------+----------------+---------------+---------------+
        |  value          |  36            |  -            |  -            |
        +-----------------+----------------+---------------+---------------+
        """

        # Creation of the DHT_SUCCESS message
        size: int = SIZE_FIELD_SIZE + MESSAGE_TYPE_FIELD_SIZE + KEY_SIZE + len(value)
        message_type: int = Message.DHT_SUCCESS
        response: bytes = struct.pack(">HH", size, message_type) + raw_key + value

        # Sending the response
        try:
            writer.write(response)
            await writer.drain()

            # Get the address of the remote peer
            remote_address, remote_port = writer.get_extra_info("socket").getpeername()
            print(f"[+] {remote_address}:{remote_port} <<< DHT_SUCCESS")
            return True

        except Exception as e:
            print(f"[-] Failed to send DHT_SUCCESS {e}")
            await bad_packet(reader, writer)
            return False


    async def handle_put_request(self, reader: StreamReader, writer: StreamWriter, body: bytes)->bool:
        """
        This method handles a put request. The Kademlia network will do its best effort to store the value in the DHT.
        :param reader: The StreamReader of the socket.
        :param writer: The StreamWriter of the socket.
        :param body: The body of the request.
        """

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
        # Extracting fields
        index=0
        ttl: int = int.from_bytes(body[index:index+TTL_FIELD_SIZE])
        index+=TTL_FIELD_SIZE
        replication: int = int.from_bytes(body[index:index+REPLICATION_FIELD_SIZE])
        index+=REPLICATION_FIELD_SIZE
        index+= RESERVED_FIELD_SIZE
        key: int = int.from_bytes(body[index:index+KEY_SIZE])
        index+=KEY_SIZE
        value: bytes = body[index:]

        # Storing the value in the network
        return await self.kademlia_service.store_value_in_network(key, ttl, value)
