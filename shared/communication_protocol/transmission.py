import socket as socket

import shared.communication_protocol.packet_builder as builder
from shared.communication_protocol.communication_errors import CommunicationError
from shared.communication_protocol.packet_analyzer import PacketInfo

PORT = 8374  # shared port
CHARSET = 'utf-8'
LFS = 5  # length field size
RECV_BUFFER_SIZE = 128000


def recv_packet(skt: socket.socket) -> PacketInfo:
    """
    Receives a packet by the transmission protocol, and returns it as a string.
    :param skt: the socket interface that we can use to communicate
    :raises ValueError: if the packet received does not follow the transmission protocol
    :return: the received packet
    """
    length = skt.recv(LFS).decode()  # receive packet length
    if not length.isnumeric():
        send_packet(skt, builder.build_packet("500", None))
        raise CommunicationError(f"Socket at address {skt.getsockname()[0]}:{str(skt.getsockname()[1])} sent a packet "
                                 f"that doesn't follow the transmission protocol")
    length = int(length)

    packet = b""
    while length > 0:
        packet += skt.recv(RECV_BUFFER_SIZE)
        length -= RECV_BUFFER_SIZE

    return PacketInfo(packet)


def gen_len_prefix(length: int) -> bytes:
    """
    Generates a prefix string for the length of the packet.
    :param length: length of the packet
    :return: a prefix string of constant length that represents the length of the packet
    """
    return str(length).zfill(LFS).encode(CHARSET)


def send_packet(skt: socket.socket, packet: bytes) -> None:
    """
    Sends a packet according transmission protocol.
    :param skt: the socket interface that we use to communicate
    :param packet: the packet to send
    """
    prefix = gen_len_prefix(len(packet))
    packet = prefix + packet
    skt.send(packet)
