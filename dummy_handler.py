import struct
import asyncio
from asyncio import StreamReader, StreamWriter


class DummyHandler:
    """
    This class is used for network testing purpose
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
        message_type = struct.unpack(">H", header[2:4])[0]

        return_status = False
        print("Message size: ", int.from_bytes(header[0:2], byteorder='big'))
        print("Message type: ", message_type)
        print("Body: ", body)


        return return_status