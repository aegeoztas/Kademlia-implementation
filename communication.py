import struct

# Size in bytes of the header fields
SIZE_FIELD_SIZE = 2
MESSAGE_TYPE_FIELD_SIZE = 2
HEADER_SIZE  = SIZE_FIELD_SIZE + MESSAGE_TYPE_FIELD_SIZE


def send_message(sock, message_type, data):
    """ Send a message with proper header """
    # Message size is the size of the data plus 4 bytes for the header (size and type)
    message = struct.pack('>HH', len(data) + HEADER_SIZE, message_type) + data

    # print("Length of the message to be sent: ", len(message))
    # print("Message to be sent: ", message)
    
    sock.sendall(message)

def receive_message(sock): 
    """ Receive a message and extract the message type and the data """

    header = sock.recv(HEADER_SIZE)
    size = int.from_bytes(header[:SIZE_FIELD_SIZE], byteorder="big")
    message_type = int.from_bytes(header[SIZE_FIELD_SIZE:], byteorder="big")

    data = sock.recv(size)

    return message_type, data