import logging
import socket
import ssl
import sys
import threading

from reedsolo import ReedSolomonError

from shared.communication_protocol.transmission import recv_packet, send_packet, PORT
from shared.communication_protocol.packet_builder import build_packet
from server.steganography.steganography_errors import SteganographyError, ContentWrapperError
from shared.communication_protocol.packet_analyzer import PacketInfo
from shared.utils import sock_name
from shared.communication_protocol.communication_errors import TransmissionProtocolError, PacketStructureError
from server.client_info import ClientInfo
from server.steganography.bpcs.engine import encode, decode


def handle_bpcs_encoding_request(client: ClientInfo, request_packet: PacketInfo):
    request_packet.verify_code("100")
    message = request_packet.body
    steg_params = request_packet.headers

    vessel_packet = recv_packet(client.socket)
    vessel_packet.verify_code("000")
    vessel_bytes = vessel_packet.body

    send_packet(client.socket, build_packet("200"))

    token, stegged_bytes = encode(vessel_bytes, message, steg_params[b"encryption-key"],
                                  ecc_block_size=int(steg_params[b"ecc-block-size"]),
                                  ecc_symbol_num=int(steg_params[b"ecc-symbol-num"]),
                                  alpha=float(steg_params[b"alpha"]))

    token_packet = build_packet("202", body=token)
    stegged_packet = build_packet("000", body=stegged_bytes)
    send_packet(client.socket, token_packet)
    send_packet(client.socket, stegged_packet)


class Server:
    def __init__(self, record_tls_secrets: bool = False):
        """
        Initializes the server socket, along with the ssl/tls wrapper, and the logging mechanisms.
        :param record_tls_secrets: Should the program record TLS secrets (for debugging purposes).
        """
        self.skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients: set[str] = set()

        self.tls_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self.tls_context.load_cert_chain(certfile="server/certificate/cert.pem",
                                         keyfile="server/certificate/cert-key.pem")
        self.tls_context.minimum_version = ssl.TLSVersion.TLSv1_3

        if record_tls_secrets:
            self.tls_context.keylog_filename = f"server/logs/secrets/secrets_log.log"

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
        try:
            while True:
                client_skt, addr = self.skt.accept()
                self.logger.info(f"Accepted connection from {sock_name(client_skt)}")
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
        client = ClientInfo(client_skt)
        try:
            if client.name in self.clients:
                client.disconnect(build_packet("403"))
                return
            self.clients.add(client.name)
            client.socket = self.tls_context.wrap_socket(client.socket, server_side=True)
            cipher, tls_version, secret_bit_num = client.socket.cipher()
            self.logger.info(f"Completed TLS handshake with client {client.name}; using {tls_version}, "
                             f"with cipher {cipher}")
            steg_request = recv_packet(client.socket)
            match steg_request.code:
                case b"100":
                    handle_bpcs_encoding_request(client, steg_request)
                case _:
                    pass

        except ConnectionError:
            # if raised, the connection is dead
            self.logger.warning(f"Client {client.name} closed the connection unexpectedly")
            client.disconnect(None)
        except ssl.SSLError as e:
            # if raised, the connection is dead
            self.logger.warning(f"A TLS connection error occurred: {e}")
            client.disconnect(None)
        except SteganographyError as e:
            self.logger.warning(f"A steganography error occurred: {e}")
            client.disconnect(build_packet("401", {"description": e.__str__()}))
        except (ContentWrapperError, ReedSolomonError) as e:
            self.logger.warning(f"A content wrapper error occurred: {e}")
            client.disconnect(build_packet("402", {"description": e.__str__()}))
        except TransmissionProtocolError as e:
            self.logger.warning(f"A transmission protocol error occurred: {e}")
            client.disconnect(build_packet("501"))
        except PacketStructureError as e:
            self.logger.warning(f"A Packet structure error occurred: {e}")
            client.disconnect(build_packet("502"))
        else:
            self.logger.info(f"Communication completed successfully with client {client.name}, "
                             f"closing the connection, and terminating client handler thread")
            client.disconnect(build_packet("500", {"reason": "end of communication"}))
        finally:
            self.clients.remove(client.name)
            self.logger.info(f"Finished handling client {client.name}")
