import socket
import struct
def connection():
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


    def connect(self):
        try:
            self.socket.connect((self.ip, self.port))
            print(f"Connected to {self.ip}:{self.port}")
        except Exception as e:
            print(f"Connection failed: {e}")
    def close(self):
        try:
            self.socket.close()
            print("Connection closed")
        except Exception as e:
            print(f"Failed to close connection: {e}")

    def send_message(sock, message_type, data):
        """ Send a message with proper header """
        # Message size is the size of the data plus 8 bytes for the header (size and type)
        # TODO add specific DHT messages for doing stuff.
        message = struct.pack('>HH', len(data) + 4, message_type) + data
        sock.sendall(message)

    def receive_message(sock, response_size):
        """ Receive a message and extract the type and data
        return data as byte so no need to turn it to bytes in a later time
    #
        """
        full_message = sock.recv(response_size)
        print(f"recieved message:{full_message}")
        # Unpack the header from the first 8 bytes
        size = int.from_bytes(full_message[:2], byteorder='big')
        message_type = int.from_bytes(full_message[2:4], byteorder='big')
        data = full_message[4:size]
        #TODO add differencaiting logic for different DHT responses
        return message_type, data

