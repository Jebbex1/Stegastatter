import logging
import socket
import ssl
import sys
import threading
from datetime import datetime

import shared.communication_protocol.transmission as transmission
import shared.communication_protocol.packet_analyzer as analyzer
import shared.communication_protocol.packet_builder as builder
from shared import utils


def get_server_logger(log_to_file: bool):
    start_time = datetime.now().strftime("%d-%m-%Y")

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if log_to_file:
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        handler = logging.FileHandler(f"server/logs/runtime/{start_time}.log")
    else:
        formatter = logging.Formatter("%(levelname)s %(message)s")
        handler = logging.StreamHandler(sys.stdout)

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


class Server:
    def __init__(self, log_to_file: bool, record_tls_secrets: bool = False):
        """
        Initializes the server socket, along with the ssl/tls wrapper, and the logging mechanisms.
        :param record_tls_secrets: Should the program record TLS secrets (for debugging purposes).
        """
        self.skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.tls_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self.tls_context.load_cert_chain(certfile="server/certificate/cert.pem",
                                         keyfile="server/certificate/cert-key.pem")
        self.tls_context.minimum_version = ssl.TLSVersion.TLSv1_3

        if record_tls_secrets:
            self.tls_context.keylog_filename = f"server/logs/secrets/secrets_log.log"

        self.logger = get_server_logger(log_to_file)
        self.console_lock = threading.Lock()  # incase we want to print something across multiple threads

    def start(self) -> None:
        """
        Starts listening to the agreed port, accepting clients one after the other. When a client connect, starts a
        thread to handle the client and its connection.
        """
        self.logger.info("Starting server...")
        self.skt.bind(('0.0.0.0', transmission.PORT))
        self.skt.listen()
        self.logger.info("Listening for connections...")
        try:
            while True:
                client_skt, addr = self.skt.accept()
                self.logger.info(f"Accepted connection from {utils.skt_addr(client_skt)}")
                threading.Thread(target=self.handle_client, args=(client_skt,)).start()
        except KeyboardInterrupt:
            self.logger.info("Server closed")

    def handle_client(self, client_skt: socket.socket) -> None:
        """
        A method to handle a client connection. Initiates ssl/tls handshake with the client, then does stuff (I left it
        empty because this is a template project). Handles any intentionally raised exception along with any connection
        or ssl/tls errors.
        :param client_skt: the socket interface to wrap with a ssl/tls layer
        """
        try:
            client_skt = self.tls_context.wrap_socket(client_skt, server_side=True)
            cipher, tls_version, secret_bit_num = client_skt.cipher()
            self.logger.info(f"Completed TLS handshake with client {utils.skt_addr(client_skt)}; using {tls_version}, "
                             f"with cipher {cipher}")

            print(transmission.recv_packet(client_skt))

            # Do stuff
            pass

        except ConnectionError:
            # client disconnected and its socket raised a ConnectionError while trying to send or read data through it
            self.logger.warning(f"Client {utils.skt_addr(client_skt)} closed the connection unexpectedly")
            self.console_log(f"Client {utils.skt_addr(client_skt)} closed the connection unexpectedly")
            self.disconnect_client(client_skt)

        except ssl.SSLError as e:
            self.logger.warning(f"There was an error regarding the TLS connection: {e}")
            self.disconnect_client(client_skt)

        else:
            self.logger.info(f"Communication completed successfully with client {utils.skt_addr(client_skt)}, "
                             f"closing the connection, and terminating client handler thread")
            self.disconnect_client(client_skt)

    def disconnect_client(self, client_skt: socket.socket) -> None:
        """
        Disconnects from a client. This is a method incase there's a need to implement additional logic before any
        time a client is disconnected.
        :param client_skt: the socket interface we want to disconnect from
        """
        self.logger.info(f"Disconnecting client {utils.skt_addr(client_skt)}")
        client_skt.close()

    def console_log(self, out) -> None:
        """
        :param out: what to write to the console via mutex
        """
        self.console_lock.acquire()
        print(str(out) + "\n")
        self.console_lock.release()


if __name__ == '__main__':
    server = Server(False)
    server.start()
