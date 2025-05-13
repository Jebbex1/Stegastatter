import copyreg
import logging
import multiprocessing
import socket
import ssl
import sys


from server.client_handler import ClientHandler
from shared.communication_protocol.constants import PORT
from shared.utils import sock_name, save_ssl_context


class Server:
    def __init__(self, record_tls_secrets: bool = False):
        """
        Initializes the server socket, along with the ssl/tls wrapper, and the logging mechanisms.
        :param record_tls_secrets: Should the program record TLS secrets (for debugging purposes).
        """
        self.skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.record_tls_secrets = record_tls_secrets

        self.logger = logging.getLogger("server_console")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(logging.StreamHandler(sys.stdout))

    def start(self) -> None:
        """
        Starts listening to the agreed port, accepting clients one after the other. When a client connect, starts a
        thread to handle the client and its connection.
        """
        self.logger.info("Starting server...")
        self.skt.bind(('0.0.0.0', PORT))
        self.skt.listen()
        self.logger.info("Listening for connections...")
        copyreg.pickle(ssl.SSLContext, save_ssl_context)
        try:
            while True:
                client_skt, addr = self.skt.accept()
                self.logger.info(f"Accepted connection from {sock_name(client_skt)}")
                subprocess = multiprocessing.Process(target=ClientHandler, args=(client_skt, self.record_tls_secrets))
                subprocess.start()
        except KeyboardInterrupt:
            self.logger.info("Server closed")
