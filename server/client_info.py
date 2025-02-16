import logging
import socket
import ssl
import threading

from shared.utils import sock_name
from shared.communication_protocol.transmission import send_packet
from shared.communication_protocol.packet_builder import build_packet


class ClientInfo:
    def __init__(self, client_skt: socket.socket):
        self.socket: socket.socket | ssl.SSLSocket = client_skt
        self.name = sock_name(self.socket)
        client_update_logger = logging.getLogger(str(threading.get_ident()))
        client_update_logger.setLevel(logging.INFO)
        client_update_logger.addFilter(self.update_status)

    def update_status(self, record: logging.LogRecord):
        send_packet(self.socket, build_packet("201", {"status": record.getMessage()}))
        return True

    def disconnect(self, disconnect_packet: bytes | None):
        logger = logging.getLogger("server_console")
        logger.info(f"Disconnecting client {self.name}")
        if disconnect_packet is not None:
            try:
                send_packet(self.socket, disconnect_packet)
            except (ConnectionError, ssl.SSLError):
                pass
        self.socket.close()
