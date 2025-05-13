import logging
import os
import socket
import ssl
import multiprocessing
import threading

from shared.communication_protocol.packet_analyzer import PacketInfo
from shared.communication_protocol.transmission import send_packet, recv_packet
from shared.communication_protocol.constants import PORT
from shared.communication_protocol.packet_builder import build_packet
from shared.utils import get_image_bytes, get_dissconnect_packet_line


def new_server_connection(server_ip: str):
    status_logger = multiprocessing.get_logger()
    skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    tls_context.load_verify_locations("shared/certificate_authority/ca-cert.pem")
    tls_context.minimum_version = ssl.TLSVersion.TLSv1_3

    status_logger.info("Connecting to server...")
    skt.connect((server_ip, PORT))
    status_logger.info("Connection successful")
    skt = tls_context.wrap_socket(skt, server_hostname=server_ip)
    status_logger.info("TLS handshake successful")

    return skt


class ClientConnection:
    def __init__(self, server_ip: str, thread_lock: threading.Lock):
        self.server_ip = server_ip
        self.thread_lock = thread_lock
        self.skt: socket.socket | None = None
        self.running = True

    def synced_thread_recv_packet(self, skt: socket.socket) -> PacketInfo:
        if self.thread_lock.locked():
            skt.close()
            exit(0)

        try:
            return recv_packet(skt)
        except TimeoutError:
            skt.close()
            exit(0)

    def synced_thread_send_packet(self, skt: socket.socket, packet: bytes) -> None:
        if self.thread_lock.locked():
            skt.close()
            exit(0)

        try:
            send_packet(skt, packet)
        except TimeoutError:
            skt.close()
            exit(0)

    def initiate_terminatation_protocol(self):
        self.thread_lock.acquire()
        if self.skt is not None and self.running:
            self.skt.settimeout(0.001)

    def end_of_thread(self):
        self.running = False
        status_logger = multiprocessing.get_logger()
        status_logger.info("Connection with server terminated.")
        status_logger.log(logging.DEBUG, "done")

    def initiate_bpcs_encoding_request(self, vessel_image_path: str, image_output_path: str, message_file_path: str,
                                       token_output_path: str, encryption_key: str, ecc_block_size: int,
                                       ecc_symbol_size: int, alpha: float) -> None:
        status_logger = multiprocessing.get_logger()
        try:
            self.skt = new_server_connection(self.server_ip)
            params_dict = {
                "encryption-key": encryption_key,
                "ecc-block-size": str(ecc_block_size),
                "ecc-symbol-num": str(ecc_symbol_size),
                "alpha": str(alpha),
            }

            vessel_image_bytes = get_image_bytes(vessel_image_path)

            request_packet = build_packet("100", headers=params_dict, body=vessel_image_bytes)
            message_packet = build_packet("000", body=open(message_file_path, "rb").read())

            self.synced_thread_send_packet(self.skt, request_packet)
            self.synced_thread_send_packet(self.skt, message_packet)

            while True:
                packet = self.synced_thread_recv_packet(self.skt)

                match packet.code:
                    case "000":
                        status_logger.info("Received BPCS token image from server!")
                        open(token_output_path, "wb").write(packet.body)
                    case "200":
                        status_logger.info("Server accepted BPCS encoding request!")
                    case "201":
                        status_logger.info(packet.headers["status"])
                    case "202":
                        status_logger.info("Received BPCS encoded from server!")
                        open(image_output_path, "wb").write(packet.body)
                    case "500":
                        status_logger.info(get_dissconnect_packet_line(packet))
                        break
                    case _:
                        if packet.code[0] == "4" or packet.code[0] == "5":
                            status_logger.info(f"An error occurred: {get_dissconnect_packet_line(packet)}")
                            break
            status_logger.info(f"Disconnecting from server...")
            self.skt.close()

            self.end_of_thread()

        except ConnectionError:
            status_logger.info("Server closed connection unexpectedly.")
        except ssl.SSLError as e:
            status_logger.info(f"There was en error regarding the TLS connection {e}")

    def initiate_lsb_encoding_request(self, vessel_image_path: str, image_output_path: str, message_file_path: str,
                                      token_output_path: str, encryption_key: str, ecc_block_size: int,
                                      ecc_symbol_size: int, num_of_sacrificed_bits: int) -> None:
        status_logger = multiprocessing.get_logger()
        try:
            self.skt = new_server_connection(self.server_ip)
            params_dict = {
                "encryption-key": encryption_key,
                "ecc-block-size": str(ecc_block_size),
                "ecc-symbol-num": str(ecc_symbol_size),
                "number-of-sacrificed-bits": str(num_of_sacrificed_bits),
            }

            vessel_image_bytes = get_image_bytes(vessel_image_path)

            request_packet = build_packet("101", headers=params_dict, body=vessel_image_bytes)
            message_packet = build_packet("000", body=open(message_file_path, "rb").read())

            self.synced_thread_send_packet(self.skt, request_packet)
            self.synced_thread_send_packet(self.skt, message_packet)

            while True:
                packet = self.synced_thread_recv_packet(self.skt)

                match packet.code:
                    case "000":
                        status_logger.info("Received LSB token image from server!")
                        open(token_output_path, "wb").write(packet.body)
                    case "200":
                        status_logger.info("Server accepted LSB encoding request!")
                    case "201":
                        status_logger.info(packet.headers["status"])
                    case "202":
                        status_logger.info("Received LSB encoded image from server!")
                        open(image_output_path, "wb").write(packet.body)
                    case "500":
                        status_logger.info(get_dissconnect_packet_line(packet))
                        break
                    case _:
                        if packet.code[0] == "4" or packet.code[0] == "5":
                            status_logger.info(f"An error occurred: {get_dissconnect_packet_line(packet)}")
                            break

            status_logger.info(f"Disconnecting from server...")
            self.skt.close()

            self.end_of_thread()

        except ConnectionError:
            status_logger.info("Server closed connection unexpectedly.")
        except ssl.SSLError as e:
            status_logger.info(f"There was en error regarding the TLS connection {e}")

    def initiate_decoding_request(self, stegged_image_path: str, message_output_path: str, token_path: str) -> None:
        status_logger = multiprocessing.get_logger()
        try:
            self.skt = new_server_connection(self.server_ip)
            stegged_image_bytes = get_image_bytes(stegged_image_path)
            token_bytes = open(token_path, "rb").read()

            request_packet = build_packet("120", body=stegged_image_bytes)
            token_packet = build_packet("000", body=token_bytes)

            self.synced_thread_send_packet(self.skt, request_packet)
            self.synced_thread_send_packet(self.skt, token_packet)

            while True:
                packet = self.synced_thread_recv_packet(self.skt)
                match packet.code:
                    case "200":
                        status_logger.info("Server accepted decoding request!")
                    case "201":
                        status_logger.info(packet.headers["status"])
                    case "203":
                        status_logger.info("Received decoded data from server!")
                        open(message_output_path, "wb").write(packet.body)
                    case "500":
                        status_logger.info(get_dissconnect_packet_line(packet))
                        break
                    case _:
                        if packet.code[0] == "4" or packet.code[0] == "5":
                            status_logger.info(f"An error occurred: {get_dissconnect_packet_line(packet)}")
                            break

            status_logger.info(f"Disconnecting from server...")
            self.skt.close()

            self.end_of_thread()

        except ConnectionError:
            status_logger.info("Server closed connection unexpectedly.")
        except ssl.SSLError as e:
            status_logger.info(f"There was en error regarding the TLS connection {e}")

    def initiate_bpcs_max_capacity_request(self, image_path: str, ecc_block_size: int,
                                           ecc_symbol_num: int, min_alpha: float) -> None:
        status_logger = multiprocessing.get_logger()
        try:
            self.skt = new_server_connection(self.server_ip)

            image_bytes = get_image_bytes(image_path)

            headers = {
                "ecc-block-size": str(ecc_block_size),
                "ecc-symbol-num": str(ecc_symbol_num),
                "alpha": str(min_alpha),
            }
            request_packet = build_packet("140", headers=headers, body=image_bytes)

            self.synced_thread_send_packet(self.skt, request_packet)

            while True:
                packet = self.synced_thread_recv_packet(self.skt)
                match packet.code:
                    case "200":
                        status_logger.info("Server accepted BPCS capacity check request!")
                    case "201":
                        status_logger.info(packet.headers["status"])
                    case "204":
                        max_capacity = int(packet.headers["max-bytes-capacity"])
                        status_logger.info(f"The selected image has a max capacity of {max_capacity} bytes using BPCS "
                                           f"steganography with the following parameters:\n"
                                           f"BPCS Minimum Complexity Coefficient: {min_alpha}\n"
                                           f"RSC Block Size: {ecc_block_size}\n"
                                           f"RSC Symbol Number: {ecc_symbol_num}\n")
                    case "500":
                        status_logger.info(get_dissconnect_packet_line(packet))
                        break
                    case _:
                        if packet.code[0] == "4" or packet.code[0] == "5":
                            status_logger.info(f"An error occurred: {get_dissconnect_packet_line(packet)}")
                            break

            status_logger.info(f"Disconnecting from server...")
            self.skt.close()

            self.end_of_thread()

        except ConnectionError:
            status_logger.info("Server closed connection unexpectedly.")
        except ssl.SSLError as e:
            status_logger.info(f"There was en error regarding the TLS connection {e}")

    def initiate_lsb_max_capacity_request(self, image_path: str, ecc_block_size: int, ecc_symbol_num: int,
                                          num_of_sacrificed_bits: int) -> None:
        status_logger = multiprocessing.get_logger()
        try:
            self.skt = new_server_connection(self.server_ip)

            image_bytes = get_image_bytes(image_path)

            headers = {
                "ecc-block-size": str(ecc_block_size),
                "ecc-symbol-num": str(ecc_symbol_num),
                "number-of-sacrificed-bits": str(num_of_sacrificed_bits),
            }
            request_packet = build_packet("141", headers=headers, body=image_bytes)

            self.synced_thread_send_packet(self.skt, request_packet)

            while True:
                packet = self.synced_thread_recv_packet(self.skt)
                match packet.code:
                    case "200":
                        status_logger.info("Server accepted LSB capacity check request!")
                    case "201":
                        status_logger.info(packet.headers["status"])
                    case "204":
                        max_capacity = int(packet.headers["max-bytes-capacity"])
                        status_logger.info(f"The selected image has a max capacity of {max_capacity} bytes using BPCS"
                                           f"steganography with the following parameters:\n"
                                           f"LSB Number of Sacrificed Bits: {num_of_sacrificed_bits}\n"
                                           f"RSC Block Size: {ecc_block_size}\n"
                                           f"RSC Symbol Number: {ecc_symbol_num}\n")
                    case "500":
                        status_logger.info(get_dissconnect_packet_line(packet))
                        break
                    case _:
                        if packet.code[0] == "4" or packet.code[0] == "5":
                            status_logger.info(f"An error occurred: {get_dissconnect_packet_line(packet)}")
                            break

            status_logger.info(f"Disconnecting from server...")
            self.skt.close()

            self.end_of_thread()

        except ConnectionError:
            status_logger.info("Server closed connection unexpectedly.")
        except ssl.SSLError as e:
            status_logger.info(f"There was en error regarding the TLS connection {e}")

    def initiate_bitplane_slicing_request(self, image_path: str, output_directory_path: str) -> None:
        status_logger = multiprocessing.get_logger()
        try:
            self.skt = new_server_connection(self.server_ip)

            os.makedirs(output_directory_path, exist_ok=True)
            image_bytes = get_image_bytes(image_path)

            request_packet = build_packet("160", body=image_bytes)
            self.synced_thread_send_packet(self.skt, request_packet)

            while True:
                packet = self.synced_thread_recv_packet(self.skt)
                match packet.code:
                    case "200":
                        status_logger.info("Server accepted BPCS capacity check request!")
                    case "201":
                        status_logger.info(packet.headers["status"])
                    case "260":
                        bitplane_slice = open(f"{output_directory_path}/{packet.headers["image-name"]}", "wb")
                        bitplane_slice.write(packet.body)
                    case "500":
                        status_logger.info(get_dissconnect_packet_line(packet))
                        break
                    case _:
                        if packet.code[0] == "4" or packet.code[0] == "5":
                            status_logger.info(f"An error occurred: {get_dissconnect_packet_line(packet)}")
                            break

            status_logger.info(f"Disconnecting from server...")
            self.skt.close()

            self.end_of_thread()

        except ConnectionError:
            status_logger.info("Server closed connection unexpectedly.")
        except ssl.SSLError as e:
            status_logger.info(f"There was en error regarding the TLS connection {e}")

    def initiate_image_diff_request(self, image1_path: str, image2_path: str,
                                    exact_diff: bool, diff_image_path: str) -> None:
        status_logger = multiprocessing.get_logger()
        try:
            self.skt = new_server_connection(self.server_ip)

            image1_bytes = get_image_bytes(image1_path)
            image2_bytes = get_image_bytes(image2_path)

            request_packet = build_packet("161", headers={"show-exact-diff": str(int(exact_diff))}, body=image1_bytes)
            second_image_packet = build_packet("000", body=image2_bytes)

            self.synced_thread_send_packet(self.skt, request_packet)
            self.synced_thread_send_packet(self.skt, second_image_packet)

            while True:
                packet = self.synced_thread_recv_packet(self.skt)
                match packet.code:
                    case "200":
                        status_logger.info("Server accepted image difference calculation request!")
                    case "201":
                        status_logger.info(packet.headers["status"])
                    case "261":
                        status_logger.info("Received difference image from server!")
                        status_logger.info(f"Red channel max difference: {packet.headers["red-diff"]}")
                        status_logger.info(f"Green channel max difference: {packet.headers["green-diff"]}")
                        status_logger.info(f"Blue channel max difference: {packet.headers["blue-diff"]}")
                        open(diff_image_path, "wb").write(packet.body)
                    case "500":
                        status_logger.info(get_dissconnect_packet_line(packet))
                        break
                    case _:
                        if packet.code[0] == "4" or packet.code[0] == "5":
                            status_logger.info(f"An error occurred: {get_dissconnect_packet_line(packet)}")
                            break
            status_logger.info(f"Disconnecting from server...")
            self.skt.close()

            self.end_of_thread()

        except ConnectionError:
            status_logger.info("Server closed connection unexpectedly.")
        except ssl.SSLError as e:
            status_logger.info(f"There was en error regarding the TLS connection {e}")
