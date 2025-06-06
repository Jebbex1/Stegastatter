import socket as socket

from shared.communication_protocol.communication_errors import TransmissionProtocolError
from shared.communication_protocol.constants import CHARSET, LFS, RECV_BUFFER_SIZE
from shared.communication_protocol.packet_analyzer import PacketInfo


def recv_packet(skt: socket.socket, validate_sizes: bool = False) -> PacketInfo:
    """
    Receives a packet by the transmission protocol, and returns it as a string.
    :param validate_sizes: should the
    :param skt: the socket interface that we can use to communicate
    :return: the received packet
    """
    length = skt.recv(LFS).decode()  # receive packet length
    if not length.isnumeric():
        raise TransmissionProtocolError(f"Socket at address {skt.getsockname()[0]}:{str(skt.getsockname()[1])} sent a "
                                        f"packet that doesn't follow the transmission protocol")
    length = int(length)

    packet = b""
    while len(packet) != length:
        packet += skt.recv(min(RECV_BUFFER_SIZE, length - len(packet)))

    packet = PacketInfo(packet)

    if validate_sizes:
        packet.validate_content_size()

    return packet


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
