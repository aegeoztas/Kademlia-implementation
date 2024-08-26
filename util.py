import hexdump

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
