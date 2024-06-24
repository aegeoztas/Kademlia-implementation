import hexdump
import socket
import struct
import sys


# def sync_bad_packet(buf, sock, reason="Unknown or malformed data received"):
#     """
#     This method is called when a response packet has the wrong format.
#     It closes the socket and terminates the process.
#     :param buf: The content of the response packet
#     :param sock: The socket.
#     :param reason: The reason for the error that will be printed.
#     :return: (void)
#     """
#     print(f"[-] {reason}:")
#     hexdump.hexdump(buf)
#     print("[-] Exiting.")
#     sock.close()
#     sys.exit(-1)
#
#
# def connect_socket(addr, port):
#     """
#     This function connects to a remote peer with the ip and port passed
#     as parameters and returns the socket.
#     :param addr: The ip address of the remote peer
#     :param port: The port of the remote peer
#     :return: The socket of the established connection
#     """
#     s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     s.connect((addr, port))
#     return s
#
#
# def sync_read_message(s, fail_reason="Server closed the connection"):
#     """
#     This method is used to receive a message synchronously.
#     :param s: The socket.
#     :param fail_reason: The message that will be printed in case of failure
#     :return: A buffer containing the content of the message (with the size field)
#     """
#     try:
#         msizebuf = s.recv(2)
#         buflen = struct.unpack(">H", msizebuf)[0]
#         buf = msizebuf + s.recv(buflen - 2)
#     except Exception as e:
#         if msizebuf != b'':
#             sync_bad_packet(buf, s, str(e))
#         else:
#             sync_bad_packet(b'', s, fail_reason)
#     return buf


async def bad_packet(reader, writer, reason='', data=b'', cleanup_func=None):
    """
    This method is called when a response packet has the wrong format. This time the function
    is asynchronous.
    :param reader: The reader to read messages from the socket.
    :param writer: The writer to write messages to the socket
    :param reason: The message printed for the failure
    :param data: The content of the packet.
    :param cleanup_func: A function that is supposed to clean up after the failure.
    :return: (void)
    """
    try:
        raddr, rport = writer.get_extra_info('socket').getpeername()
    except OSError:
        writer.close()
        await writer.wait_closed()
        print(f"[i] (Unknown) xxx Connection closed abruptly, state may remain")
        return

    if reason != '':
        print(f"[-] {raddr}:{rport} >>> {reason}:\n")
        hexdump.hexdump(data)
        print('')

    if cleanup_func:
        await cleanup_func((reader, writer))

    writer.close()
    await writer.wait_closed()
    print(f"[i] {raddr}:{rport} xxx Connection closed")


async def read_message(reader, writer, cleanup_func=None):
    """
    This method is used to receive messages asynchronously.
    :param reader: The reader of the socket.
    :param writer: The writer of the socket.
    :param cleanup_func: cleanup function for the error management.
    :return: a buffer containing the whole message.
    """
    if writer.is_closing():
        await bad_packet(reader, writer, cleanup_func=cleanup_func)
        return b''

    try:
        raddr, rport = writer.get_extra_info('socket').getpeername()
    except OSError:
        await bad_packet(reader, writer, cleanup_func=cleanup_func)
        return b''

    try:
        msizebuf = await reader.read(2)
        buflen = struct.unpack(">H", msizebuf)[0]
        buf = msizebuf + await reader.read(buflen)
    except Exception as e:
        if msizebuf != b'':
            await bad_packet(reader, writer,
                             "Malformed data received", msizebuf, cleanup_func)
        else:
            await bad_packet(reader, writer, cleanup_func=cleanup_func)

        buf = b''
    return buf


async def handle_client(reader, writer, handle_message, cleanup_func=None):
    """
    This method handles the connection of a new client.
    :param reader: The reader of the socket.
    :param writer: The writer of the socket.
    :param handle_message: The handler responsible for processing messages
    :param cleanup_func: Function responsible to clean up after errors.
    :return: (void)
    """
    raddr, rport = writer.get_extra_info('socket').getpeername()
    print(f"[+] {raddr}:{rport} >>> Incoming connection")

    while True:
        buf = await read_message(reader, writer, cleanup_func=cleanup_func)
        if buf == b'':
            return

        if not await handle_message(buf, reader, writer):
            return
