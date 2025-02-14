import socket
from datetime import datetime


def sock_name(skt: socket.socket) -> str:
    """
    Get socket address in the format ipv4:port
    :param skt: the socket interface we want to get the address of
    :return: sockets' address in the format ipv4:port
    """
    return skt.getsockname()[0] + ":" + str(skt.getsockname()[1])


def ftime():
    return datetime.now().strftime("%d-%m-%Y %H:%M:%S.%f")[:-3]
