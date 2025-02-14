import socket
import ssl

import shared.communication_protocol.transmission as transmission
import shared.communication_protocol.packet_analyzer as analyzer
import shared.communication_protocol.packet_builder as builder
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
            self.skt.connect((server_ipv4, transmission.PORT))  # initial connection
            print("Connection successful")
            self.skt = self.tls_context.wrap_socket(self.skt, server_hostname=server_ipv4)
            print("TLS handshake successful")

            transmission.send_packet(self.skt, b"HELLOOOOO")

        except ValueError as e:
            # intentionally raised value error - server did something that caused a problem
            print(e)
            self.disconnect()
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


if __name__ == '__main__':
    client = Client()
    client.start('127.0.0.1')
