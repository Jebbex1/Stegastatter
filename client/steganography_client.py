import socket
import ssl
import time

from shared.communication_protocol.transmission import PORT, send_packet, recv_packet
from shared.communication_protocol.packet_analyzer import PacketInfo
from shared.communication_protocol.packet_builder import build_packet
from shared import utils


class Client:
    """
    A basic client that knows how to communicate with the server
    """

    def __init__(self):
        """
        Initializes the server socket, along with the ssl/tls wrapper.
        """
        self.skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.tls_context.load_verify_locations("shared/certificate-authority/ca-cert.pem")
        self.tls_context.minimum_version = ssl.TLSVersion.TLSv1_3

    def start(self, server_ipv4: str) -> None:
        """
        The method that manages the connection to the server. Initiates ssl/tls handshake with the server, then does
        stuff (I left it empty because this is a template project). Handles any intentionally raised exception along
        with any connection or ssl/tls errors.
        :param server_ipv4: the servers' ipv4 address
        """
        try:
            print("Connecting to server...")
            self.skt.connect((server_ipv4, PORT))  # initial connection
            print("Connection successful")
            self.skt = self.tls_context.wrap_socket(self.skt, server_hostname=server_ipv4)
            print("TLS handshake successful")

            params_dict = {"encryption-key": "hello there",
                           "ecc-block-size": "255",
                           "ecc-symbol-num": "16",
                           "alpha": "0.3", }

            message = b"helooooo"

            request = build_packet("100", headers=params_dict, body=message)
            vessel = build_packet("000", body=(open("assets/ves2.png", "rb").read()))

            send_packet(self.skt, request)
            send_packet(self.skt, vessel)

            token = b""

            while True:
                packet = recv_packet(self.skt)
                match packet.code.decode():
                    case "201":
                        print(packet.headers[b"status"].decode())
                    case "202":
                        print("Got token")
                        token = packet.body
                    case "000":
                        print("Got image")
                        open("assets/out1.png", "wb").write(packet.body)
                    case "500":
                        break


        except ConnectionError:
            # server disconnected
            print("Server closed connection")
            self.disconnect()
        except ssl.SSLError as e:
            print(f"There was en error regarding the TLS connection {e}")

    def disconnect(self) -> None:
        """
        Disconnects from the server; closes the socket
        """
        print(f"Disconnecting from server")
        self.skt.close()
