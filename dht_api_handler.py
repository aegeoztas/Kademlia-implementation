import os

from LocalNode import LocalNode
from kademlia_handler import DHTHandler, KademliaHandler
from asyncio.streams import StreamReader, StreamWriter
from util import *
from MessageTypes import Message

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





class DHT_APIHandler ( DHTHandler):
    """
    The role of this class is to handle incoming messages that are
    reaching the local node and using DHT API
    """

    def __init__(self, local_node: LocalNode, kademlia_handler: KademliaHandler):
        # self.local_node: LocalNode = local_node
        # it doesn't make sense for dht handler to have it's own local node

        super().__init__(local_node,kademlia_handler)
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

            # needs to send a kademlia get message.
            # better to start working there
            find_value_response = await self.k_handler.handle_find_value_request(reader, writer, key)
            # this way as we pass the reader / writer this will be handled on kademlia interface
            # kademlia handler will act as it got FIND_VALUE request
            # if it finds the value it returns true and sends the key value pair back to the passed reader/writer
            # as we use same message types for dht_get-find_value and their respective success failure responses
            # it will be seamless
            # if it can't find it, it will return kbucket of closest nodes.

            if find_value_response == True:
                return True
            else:
                return False

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
        return_value = self.k_handler.handle_store_request(reader=reader, writer =writer, ttl=ttl,replication=replication,key=key,value=value)
        return return_value