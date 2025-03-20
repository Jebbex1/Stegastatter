import logging
import socket
import ssl
import multiprocessing as mp
import sys

from server.steganography.content_wrapper.wrapper import Algorithms, TokenError
from server.steganography.lsb.engine import lsb_encode, lsb_decode, lsb_check_if_fits_from_arbitrary
from shared.communication_protocol.transmission import recv_packet, send_packet
from shared.communication_protocol.packet_builder import build_packet
from server.steganography.steganography_errors import SteganographyError, ContentWrapperError
from shared.communication_protocol.packet_analyzer import PacketInfo
from shared.utils import sock_name
from shared.communication_protocol.communication_errors import TransmissionProtocolError, PacketStructureError, \
    PacketContentsError
from server.steganography.bpcs.engine import bpcs_encode, bpcs_decode, bpcs_check_if_fits_from_arbitrary
from server.steganography.steganalysis.bit_plane_slicing import slice_rgb_bit_planes
from server.steganography.steganalysis.get_diff import show_diff
from reedsolo import ReedSolomonError


class ClientHandler:
    def __init__(self, client_skt: socket.socket, record_tls_secrets: bool):
        self.socket: socket.socket | ssl.SSLSocket = client_skt
        self.name = sock_name(self.socket)

        self.console_logger = logging.getLogger("server_console")
        self.console_logger.setLevel(logging.INFO)
        self.console_logger.addHandler(logging.StreamHandler(stream=sys.stdout))

        client_update_logger = mp.get_logger()
        client_update_logger.setLevel(logging.INFO)
        client_update_logger.addFilter(self.update_status)

        self.tls_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self.tls_context.load_cert_chain(certfile="server/certificate/cert.pem",
                                         keyfile="server/certificate/cert-key.pem")
        self.tls_context.minimum_version = ssl.TLSVersion.TLSv1_3

        if record_tls_secrets:
            self.tls_context.keylog_filename = f"server/logs/secrets/secrets_log.log"

        self.is_alive = True

        self.handle_client()

    def wrap_tls(self):
        self.socket = self.tls_context.wrap_socket(self.socket, server_side=True)
        cipher, tls_version, secret_bit_num = self.socket.cipher()
        self.console_logger.info(f"Completed TLS handshake with client {self.name}; using {tls_version}, "
                                 f"with cipher {cipher}")

    def update_status(self, record: logging.LogRecord):
        if self.is_alive:
            send_packet(self.socket, build_packet("201", {"status": record.getMessage()}))
        return self.is_alive

    def handle_client(self) -> None:
        self.socket.settimeout(10)
        try:
            self.wrap_tls()
            request_packet = recv_packet(self.socket)
            match request_packet.code:
                case "100": self.handle_bpcs_encoding_request(request_packet)
                case "101": self.handle_lsb_encoding_request(request_packet)
                case "120": self.handle_decoding_request(request_packet)
                case "140": self.handle_bpcs_capacity_request(request_packet)
                case "141": self.handle_lsb_capacity_request(request_packet)
                case "160": self.handle_bitplane_slicing_request(request_packet)
                case "161": self.handle_image_diff_request(request_packet)
                case _:
                    pass

        except ConnectionError:
            # if raised, the connection is dead
            self.console_logger.warning(f"Client {self.name} closed the connection unexpectedly")
            self.disconnect(None)
        except TimeoutError:
            self.console_logger.warning(f"Client {self.name} took too long to respond.")
            self.disconnect(None)
        except ssl.SSLError as e:
            # if raised, the connection is dead
            self.console_logger.warning(f"A TLS connection error occurred: {e}")
            self.disconnect(None)
        except SteganographyError as e:
            self.console_logger.warning(f"A steganography error occurred: {e}")
            self.disconnect(build_packet("401", {"description": e.__str__()}))
        except (ContentWrapperError, ReedSolomonError) as e:
            self.console_logger.warning(f"A content wrapper error occurred: {e}")
            self.disconnect(build_packet("402", {"description": e.__str__()}))
        except TransmissionProtocolError as e:
            self.console_logger.warning(f"A transmission protocol error occurred: {e}")
            self.disconnect(build_packet("501"))
        except PacketStructureError as e:
            self.console_logger.warning(f"A Packet structure error occurred: {e}")
            self.disconnect(build_packet("502"))
        except PacketContentsError as e:
            self.console_logger.warning(f"A Packet contents error occurred: {e}")
            self.disconnect(build_packet("503", {"description": e.__str__()}))
        else:
            self.console_logger.info(f"Communication completed successfully with client {self.name}, "
                                     f"closing the connection, and terminating client handler thread")
            self.disconnect(build_packet("500", {"reason": "end of communication"}))
        finally:
            self.console_logger.info(f"Finished handling client {self.name}")
            self.is_alive = False

    def handle_bpcs_encoding_request(self, request_packet: PacketInfo):
        request_packet.verify_code("100")
        vessel_bytes = request_packet.body
        params_dict = request_packet.headers

        vessel_packet = recv_packet(self.socket)
        vessel_packet.verify_code("000")
        message = vessel_packet.body

        try:
            key = params_dict["encryption-key"]
            ecc_block_size = int(params_dict["ecc-block-size"])
            ecc_symbol_num = int(params_dict["ecc-symbol-num"])
            alpha = float(params_dict["alpha"])
        except ValueError as e:
            raise PacketContentsError(f"Packet header types are invalid: {e}")

        send_packet(self.socket, build_packet("200"))

        stegged_bytes, token = bpcs_encode(vessel_bytes, message, key, ecc_block_size=ecc_block_size,
                                           ecc_symbol_num=ecc_symbol_num, alpha=alpha)

        encoding_product_packet = build_packet("202", body=stegged_bytes)
        token_packet = build_packet("000", body=token)

        send_packet(self.socket, encoding_product_packet)
        send_packet(self.socket, token_packet)

    def handle_lsb_encoding_request(self, request_packet: PacketInfo):
        request_packet.verify_code("101")
        vessel_bytes = request_packet.body
        params_dict = request_packet.headers

        vessel_packet = recv_packet(self.socket)
        vessel_packet.verify_code("000")
        message = vessel_packet.body

        try:
            key = params_dict["encryption-key"]
            ecc_block_size = int(params_dict["ecc-block-size"])
            ecc_symbol_num = int(params_dict["ecc-symbol-num"])
            num_of_sacrificed_bits = int(params_dict["number-of-sacrificed-bits"])
        except ValueError as e:
            raise PacketContentsError(f"Packet header types are invalid: {e}")

        send_packet(self.socket, build_packet("200"))

        stegged_bytes, token = lsb_encode(vessel_bytes, message, key, ecc_block_size=ecc_block_size,
                                          ecc_symbol_num=ecc_symbol_num, num_of_sacrificed_bits=num_of_sacrificed_bits)

        encoding_product_packet = build_packet("202", body=stegged_bytes)
        token_packet = build_packet("000", body=token)

        send_packet(self.socket, encoding_product_packet)
        send_packet(self.socket, token_packet)

    def handle_decoding_request(self, request_packet: PacketInfo):
        request_packet.verify_code("120")
        steged_bytes = request_packet.body

        stegged_packet = recv_packet(self.socket)
        stegged_packet.verify_code("000")
        token = stegged_packet.body

        send_packet(self.socket, build_packet("200"))

        match token[0]:
            case Algorithms.LSB: decoded_data = lsb_decode(steged_bytes, token)
            case Algorithms.BPCS: decoded_data = bpcs_decode(steged_bytes, token)
            case _:
                raise TokenError("No matching steganography algorithm for provided token.")

        products_packet = build_packet("203", body=decoded_data)

        send_packet(self.socket, products_packet)

    def handle_bpcs_capacity_request(self, request_packet: PacketInfo):
        request_packet.verify_code("140")
        params_dict = request_packet.headers
        vessel_bytes = request_packet.body

        try:
            ecc_block_size = int(params_dict["ecc-block-size"])
            ecc_symbol_num = int(params_dict["ecc-symbol-num"])
            alpha = float(params_dict["alpha"])
            message_length = int(params_dict["message-length"])
        except ValueError as e:
            raise PacketContentsError(f"Packet header types are invalid: {e}")

        send_packet(self.socket, build_packet("200"))

        can_fit = bpcs_check_if_fits_from_arbitrary(vessel_bytes, message_length, ecc_block_size, ecc_symbol_num, alpha)

        products_packet = build_packet("204", headers={"can-fit": str(can_fit)})

        send_packet(self.socket, products_packet)

    def handle_lsb_capacity_request(self, request_packet: PacketInfo):
        request_packet.verify_code("141")
        params_dict = request_packet.headers
        vessel_bytes = request_packet.body

        try:
            ecc_block_size = int(params_dict["ecc-block-size"])
            ecc_symbol_num = int(params_dict["ecc-symbol-num"])
            num_of_sacrificed_bits = int(params_dict["number-of-sacrificed-bits"])
            message_length = int(params_dict["message-length"])
        except ValueError as e:
            raise PacketContentsError(f"Packet header types are invalid: {e}")

        send_packet(self.socket, build_packet("200"))

        can_fit = lsb_check_if_fits_from_arbitrary(vessel_bytes, message_length, ecc_block_size, ecc_symbol_num,
                                                   num_of_sacrificed_bits)

        products_packet = build_packet("204", headers={"can-fit": str(can_fit)})

        send_packet(self.socket, products_packet)

    def handle_bitplane_slicing_request(self, request_packet: PacketInfo):
        request_packet.verify_code("160")
        image_bytes = request_packet.body

        send_packet(self.socket, build_packet("200"))

        slices = slice_rgb_bit_planes(image_bytes)

        for name, slice_bytes in slices:
            slice_packet = build_packet("260", headers={"image-name": name}, body=slice_bytes)
            send_packet(self.socket, slice_packet)

    def handle_image_diff_request(self, request_packet: PacketInfo):
        request_packet.verify_code("161")
        params_dict = request_packet.headers
        image1_bytes = request_packet.body

        try:
            exact_diff = bool(int(params_dict["show-exact-diff"]))
        except ValueError as e:
            raise PacketContentsError(f"Packet header types are invalid: {e}")

        image2_packet = recv_packet(self.socket)
        image2_packet.verify_code("000")
        image2_bytes = image2_packet.body

        send_packet(self.socket, build_packet("200"))

        (r_diff, g_diff, b_diff), diff_image_bytes = show_diff(image1_bytes, image2_bytes, exact_diff)

        diff_headers = {
            "red-diff": str(r_diff),
            "green-diff": str(g_diff),
            "blue-diff": str(b_diff),
        }

        products_packet = build_packet("261", headers=diff_headers, body=diff_image_bytes)
        send_packet(self.socket, products_packet)

    def disconnect(self, disconnect_packet: bytes | None):
        logger = logging.getLogger("server_console")
        logger.info(f"Disconnecting client {self.name}")
        if disconnect_packet is not None:
            try:
                send_packet(self.socket, disconnect_packet)
            except (ConnectionError, ssl.SSLError):
                pass
        self.socket.close()
