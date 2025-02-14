import logging
import socket
import ssl

from shared.utils import sock_name
from shared.communication_protocol.transmission import send_packet
from shared.communication_protocol.packet_builder import build_packet


class ClientInfo:
    def __init__(self, client_skt: socket.socket):
        self.skt: socket.socket | ssl.SSLSocket = client_skt
        self.name = sock_name(self.skt)

    def update_status(self, status: str):
        send_packet(self.skt, build_packet("201", {"status": status}))

    def disconnect(self, disconnect_packet: bytes | None):
        logger = logging.getLogger("server_console")
        logger.info(f"Disconnecting client {self.name}")
        if disconnect_packet is not None:
            try:
                send_packet(self.skt, disconnect_packet)
            except (ConnectionError, ssl.SSLError):
                pass
        self.skt.close()
