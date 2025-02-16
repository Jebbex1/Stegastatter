import socket
from datetime import datetime
from PIL import Image
import io


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
