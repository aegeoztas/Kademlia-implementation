import socket
import struct
import asyncio


class Connection:
    def __init__(self, ip: str, port: int, timeout: int):
        self.ip: str = ip
        self.port: int = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setblocking(False)
        self.timeout: int = timeout

    async def connect(self) -> bool:
        """
        Try to connect to a remote peer.
        :return: True if the connection was successful.
        """
        loop = asyncio.get_event_loop()
        try:
            await loop.sock_connect(self.socket, (self.ip, self.port))
            print(f"Connected to {self.ip}:{self.port}")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    async def close(self) -> bool:
        """
        Close the socket
        :return: True if the operation was successful
        """
        try:
            self.socket.close()
            print("Connection closed")
            return True
        except Exception as e:
            print(f"Failed to close connection: {e}")
            return False

    async def send_message(self, message: bytes) -> bool:
        """
        Send a message.
        :param message: The message to send.
        :return: True if the operation was successful.
        """
        loop = asyncio.get_event_loop()
        try:
            await loop.sock_sendall(self.socket, message)
            print("Message sent")
            return True
        except Exception as e:
            print(f"Failed to send message: {e}")
            return False

    async def receive_message(self) -> (int, bytes):
        """ Receive a message and extract the type and data
        """
        loop = asyncio.get_event_loop()

        async def recv_exact(sock, nb_of_bytes: int):
            data_received = b''
            while len(data_received) < nb_of_bytes:
                chunk = await loop.sock_recv(sock, nb_of_bytes - len(data))
                if not chunk:
                    raise ConnectionError("Socket connection lost")
                data_received += chunk
            return data_received

        try:
            # Receive the header with a timeout
            header = await asyncio.wait_for(recv_exact(self.socket, 4), self.timeout)
            print(f"received message: {header}")

            # Unpack the header from the first 4 bytes
            size = int.from_bytes(header[:2], byteorder='big')
            message_type = int.from_bytes(header[2:4], byteorder='big')

            # Receive the remaining bytes with a timeout
            data = await asyncio.wait_for(recv_exact(self.socket, size - 2), self.timeout)

            return message_type, data

        except asyncio.TimeoutError:
            print("Timeout occurred while receiving the message")
            return None, None
