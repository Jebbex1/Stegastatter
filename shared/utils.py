import socket
from datetime import datetime
from PIL import Image
import io

from shared.communication_protocol.packet_analyzer import PacketInfo


def sock_name(skt: socket.socket) -> str:
    """
    Get socket address in the format ipv4:port
    :param skt: the socket interface we want to get the address of
    :return: sockets' address in the format ipv4:port
    """
    return skt.getsockname()[0] + ":" + str(skt.getsockname()[1])


def ftime():
    return datetime.now().strftime("%d-%m-%Y %H:%M:%S.%f")[:-3]


def get_image_bytes(image_path: str) -> bytes:
    image = Image.open(image_path)
    image_bytes = io.BytesIO()
    image.save(image_bytes, format="PNG")
    return image_bytes.getvalue()


def get_dissconnect_packet_line(packet: PacketInfo):
    match packet.code:
        case "401":
            return f"{packet.desc}: {packet.headers["description"]}"
        case "402":
            return f"{packet.desc}: {packet.headers["description"]}"
        case "500":
            return f"{packet.desc}: {packet.headers["reason"]}"
        case "503":
            return f"{packet.desc}: {packet.headers["description"]}"
        case _:
            return packet.desc


def save_ssl_context(obj):
    return obj.__class__, (obj.protocol,)



