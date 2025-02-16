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
from shared.communication_protocol.communication_errors import TransmissionProtocolError, PacketStructureError, \
    PacketContentsError
from server.client_info import ClientInfo
from server.steganography.bpcs.engine import encode, decode, check_if_fits_from_arbitrary
from server.steganography.steganalysis.bit_plane_slicing import slice_rgb_bit_planes
from server.steganography.steganalysis.get_diff import show_diff


def handle_bpcs_encoding_request(client: ClientInfo, request_packet: PacketInfo):
    request_packet.verify_code("100")
    vessel_bytes = request_packet.body
    params_dict = request_packet.headers

    vessel_packet = recv_packet(client.socket)
    vessel_packet.verify_code("000")
    message = vessel_packet.body

    try:
        key = params_dict[b"encryption-key"]
        ecc_block_size = int(params_dict[b"ecc-block-size"])
        ecc_symbol_num = int(params_dict[b"ecc-symbol-num"])
        alpha = float(params_dict[b"alpha"])
    except ValueError as e:
        raise PacketContentsError(f"Packet header types are invalid: {e}")

    send_packet(client.socket, build_packet("200"))

    stegged_bytes, token = encode(vessel_bytes, message, key, ecc_block_size=ecc_block_size,
                                  ecc_symbol_num=ecc_symbol_num, alpha=alpha)

    encoding_product_packet = build_packet("202", body=stegged_bytes)
    token_packet = build_packet("000", body=token)

    send_packet(client.socket, encoding_product_packet)
    send_packet(client.socket, token_packet)


def handle_bpcs_decoding_request(client: ClientInfo, request_packet: PacketInfo):
    request_packet.verify_code("120")
    steged_bytes = request_packet.body

    stegged_packet = recv_packet(client.socket)
    stegged_packet.verify_code("000")
    token = stegged_packet.body

    send_packet(client.socket, build_packet("200"))

    decoded_data = decode(steged_bytes, token)

    products_packet = build_packet("203", body=decoded_data)

    send_packet(client.socket, products_packet)


def handle_bpcs_capacity_request(client: ClientInfo, request_packet: PacketInfo):
    request_packet.verify_code("140")
    params_dict = request_packet.headers
    vessel_bytes = request_packet.body

    try:
        ecc_block_size = int(params_dict[b"ecc-block-size"])
        ecc_symbol_num = int(params_dict[b"ecc-symbol-num"])
        alpha = float(params_dict[b"alpha"])
        message_length = int(params_dict[b"message-length"])
    except ValueError as e:
        raise PacketContentsError(f"Packet header types are invalid: {e}")

    send_packet(client.socket, build_packet("200"))

    can_fit = check_if_fits_from_arbitrary(vessel_bytes, message_length, ecc_block_size, ecc_symbol_num, alpha)

    products_packet = build_packet("204", headers={"can-fit": str(can_fit)})

    send_packet(client.socket, products_packet)


def handle_bitplane_slicing_request(client: ClientInfo, request_packet: PacketInfo):
    request_packet.verify_code("160")
    image_bytes = request_packet.body

    send_packet(client.socket, build_packet("200"))

    client_update_logger = logging.getLogger(str(threading.get_ident()))
    client_update_logger.setLevel(logging.INFO)
    client_update_logger.addFilter(client.update_status)

    slices = slice_rgb_bit_planes(image_bytes)

    for name, slice_bytes in slices:
        slice_packet = build_packet("260", headers={"image-name": name}, body=slice_bytes)
        send_packet(client.socket, slice_packet)


def handle_image_diff_request(client: ClientInfo, request_packet: PacketInfo):
    request_packet.verify_code("161")
    params_dict = request_packet.headers
    image1_bytes = request_packet.body

    try:
        exact_diff = bool(int(params_dict[b"show-exact-diff"].decode()))
    except ValueError as e:
        raise PacketContentsError(f"Packet header types are invalid: {e}")

    image2_packet = recv_packet(client.socket)
    image2_packet.verify_code("000")
    image2_bytes = image2_packet.body

    send_packet(client.socket, build_packet("200"))

    (r_diff, g_diff, b_diff), diff_image_bytes = show_diff(image1_bytes, image2_bytes, exact_diff)

    diff_headers = {
        "red-diff": str(r_diff),
        "green-diff": str(g_diff),
        "blue-diff": str(b_diff),
    }

    products_packet = build_packet("261", headers=diff_headers, body=diff_image_bytes)
    send_packet(client.socket, products_packet)


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
        client_skt.settimeout(10)
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
            request_packet = recv_packet(client.socket)
            match request_packet.code:
                case b"100":
                    handle_bpcs_encoding_request(client, request_packet)
                case b"120":
                    handle_bpcs_decoding_request(client, request_packet)
                case b"140":
                    handle_bpcs_capacity_request(client, request_packet)
                case b"160":
                    handle_bitplane_slicing_request(client, request_packet)
                case b"161":
                    handle_image_diff_request(client, request_packet)
                case _:
                    pass

        except ConnectionError:
            # if raised, the connection is dead
            self.logger.warning(f"Client {client.name} closed the connection unexpectedly")
            client.disconnect(None)
        except TimeoutError:
            self.logger.warning(f"Client {client.name} took too long to respond.")
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
        except PacketContentsError as e:
            self.logger.warning(f"A Packet contents error occurred: {e}")
            client.disconnect(build_packet("503", {"description": e.__str__()}))
        else:
            self.logger.info(f"Communication completed successfully with client {client.name}, "
                             f"closing the connection, and terminating client handler thread")
            client.disconnect(build_packet("500", {"reason": "end of communication"}))
        finally:
            try:
                self.clients.remove(client.name)
            except KeyError:
                pass
            self.logger.info(f"Finished handling client {client.name}")
