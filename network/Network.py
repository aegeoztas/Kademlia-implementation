import socket
import struct
import asyncio
def Connection():

    async def connect(self,reader=None,writer=None):
        try:

            if reader and writer is not None:
                self.reader = reader
                self.writer = writer
            else:
                self.reader, self.writer = await asyncio.open_connection(self.ip, self.port)
            self.ip , self.port = self.writer.get_extra_info('socket').getpeername()
            print(f"[+] Accepted connection to {self.ip}:{self.port}")
        except Exception as e:
            print(f"[+] Connection failed: {e}")

    async def close(self):
        try:
            if self.writer:
                self.writer.close()
                await self.writer.wait_closed()
                print("[+] Connection closed")
        except Exception as e:
            print(f"[+] Failed to close connection: {e}")

    async def send_message(self, message_type, data):
        """ Send a message with proper header """
        # Message size is the size of the data plus 4 bytes for the header (size and type)
        message = struct.pack('>HH', len(data) + 4, message_type) + data
        self.writer.write(message)
        await self.writer.drain()



    async def receive_message(self):
        """ Receive a message and extract the type and data
        return data as byte so no need to turn it to bytes in a later time
        """
        header = self.reader.readexactly(4)
        print(f"[+] Received message header: {header}")
        # Unpack the header from the first 8 bytes
        size = int.from_bytes(header[:2], byteorder='big')
        message_type = int.from_bytes(header[2:4], byteorder='big')
        data = await self.reader.readexactly(size - 4)
        print(f"[+] Received message data: {data}")
        # Data is returned and handled with header on main.py
        return message_type, data