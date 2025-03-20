import logging
import os
import socket
import ssl
import multiprocessing

from shared.communication_protocol.transmission import PORT, send_packet, recv_packet
from shared.communication_protocol.packet_builder import build_packet
from shared.utils import get_image_bytes, get_dissconnect_packet_line


def new_server_connection(server_ip: str):
    text_logger = multiprocessing.get_logger()
    skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    tls_context.load_verify_locations("shared/certificate_authority/ca-cert.pem")
    tls_context.minimum_version = ssl.TLSVersion.TLSv1_3

    text_logger.info("Connecting to server...")
    skt.connect((server_ip, PORT))
    text_logger.info("Connection successful")
    skt = tls_context.wrap_socket(skt, server_hostname=server_ip)
    text_logger.info("TLS handshake successful")

    return skt


def initiate_bpcs_encoding_request(server_address: str, vessel_image_path: str, image_output_path: str,
                                   message_bytes: bytes, token_output_path: str, encryption_key: str,
                                   ecc_block_size: int, ecc_symbol_size: int, alpha: float) -> None:
    text_logger = multiprocessing.get_logger()
    try:
        tls_socket = new_server_connection(server_address)
        params_dict = {
            "encryption-key": encryption_key,
            "ecc-block-size": str(ecc_block_size),
            "ecc-symbol-num": str(ecc_symbol_size),
            "alpha": str(alpha),
        }

        vessel_image_bytes = get_image_bytes(vessel_image_path)

        request_packet = build_packet("100", headers=params_dict, body=vessel_image_bytes)
        message_packet = build_packet("000", body=message_bytes)

        send_packet(tls_socket, request_packet)
        send_packet(tls_socket, message_packet)

        while True:
            packet = recv_packet(tls_socket)

            match packet.code:
                case "000":
                    text_logger.info("Received BPCS token image from server!")
                    open(token_output_path, "wb").write(packet.body)
                case "200":
                    text_logger.info("Server accepted BPCS encoding request!")
                case "201":
                    text_logger.info(packet.headers["status"])
                case "202":
                    text_logger.info("Received BPCS encoded from server!")
                    open(image_output_path, "wb").write(packet.body)
                case "500":
                    text_logger.info(get_dissconnect_packet_line(packet))
                    break
                case _:
                    if packet.code[0] == "4" or packet.code[0] == "5":
                        text_logger.info(f"An error occurred: {get_dissconnect_packet_line(packet)}")
                        break
        text_logger.info(f"Disconnecting from server...")
        tls_socket.close()

    except ConnectionError:
        text_logger.info("Server closed connection unexpectedly.")
    except ssl.SSLError as e:
        text_logger.info(f"There was en error regarding the TLS connection {e}")


def initiate_lsb_encoding_request(server_address: str, vessel_image_path: str, image_output_path: str,
                                  message_bytes: bytes, token_output_path: str, encryption_key: str,
                                  ecc_block_size: int, ecc_symbol_size: int, num_of_sacrificed_bits: int):
    text_logger = multiprocessing.get_logger()
    try:
        tls_socket = new_server_connection(server_address)
        params_dict = {
            "encryption-key": encryption_key,
            "ecc-block-size": str(ecc_block_size),
            "ecc-symbol-num": str(ecc_symbol_size),
            "number-of-sacrificed-bits": str(num_of_sacrificed_bits),
        }

        vessel_image_bytes = get_image_bytes(vessel_image_path)

        request_packet = build_packet("101", headers=params_dict, body=vessel_image_bytes)
        message_packet = build_packet("000", body=message_bytes)

        send_packet(tls_socket, request_packet)
        send_packet(tls_socket, message_packet)

        while True:
            packet = recv_packet(tls_socket)

            match packet.code:
                case "000":
                    text_logger.info("Received LSB token image from server!")
                    open(token_output_path, "wb").write(packet.body)
                case "200":
                    text_logger.info("Server accepted LSB encoding request!")
                case "201":
                    text_logger.info(packet.headers["status"])
                case "202":
                    text_logger.info("Received LSB encoded from server!")
                    open(image_output_path, "wb").write(packet.body)
                case "500":
                    text_logger.info(get_dissconnect_packet_line(packet))
                    break
                case _:
                    if packet.code[0] == "4" or packet.code[0] == "5":
                        text_logger.info(f"An error occurred: {get_dissconnect_packet_line(packet)}")
                        break
        text_logger.info(f"Disconnecting from server...")
        tls_socket.close()

    except ConnectionError:
        text_logger.info("Server closed connection unexpectedly.")
    except ssl.SSLError as e:
        text_logger.info(f"There was en error regarding the TLS connection {e}")


def initiate_decoding_request(server_address: str, stegged_image_path: str, token_path: str) -> bytes:
    text_logger = multiprocessing.get_logger()
    try:
        tls_socket = new_server_connection(server_address)
        stegged_image_bytes = get_image_bytes(stegged_image_path)
        token_bytes = open(token_path, "rb").read()

        request_packet = build_packet("120", body=stegged_image_bytes)
        token_packet = build_packet("000", body=token_bytes)

        send_packet(tls_socket, request_packet)
        send_packet(tls_socket, token_packet)

        data = b""

        while True:
            packet = recv_packet(tls_socket)
            match packet.code:
                case "200":
                    text_logger.info("Server accepted decoding request!")
                case "201":
                    text_logger.info(packet.headers["status"])
                case "203":
                    text_logger.info("Received BPCS decoded data from server!")
                    data = packet.body
                case "500":
                    text_logger.info(get_dissconnect_packet_line(packet))
                    break
                case _:
                    if packet.code[0] == "4" or packet.code[0] == "5":
                        text_logger.info(f"An error occurred: {get_dissconnect_packet_line(packet)}")
                        break

        text_logger.info(f"Disconnecting from server...")
        tls_socket.close()
        return data

    except ConnectionError:
        text_logger.info("Server closed connection unexpectedly.")
    except ssl.SSLError as e:
        text_logger.info(f"There was en error regarding the TLS connection {e}")


def initiate_bpcs_capacity_check_request(server_address: str, image_path: str, message_length: int,
                                         ecc_block_size: int, ecc_symbol_size: int, alpha: float) -> bool:
    text_logger = multiprocessing.get_logger()
    try:
        tls_socket = new_server_connection(server_address)

        image_bytes = get_image_bytes(image_path)

        headers = {
            "ecc-block-size": str(ecc_block_size),
            "ecc-symbol-num": str(ecc_symbol_size),
            "alpha": str(alpha),
            "message-length": str(message_length),
        }
        request_packet = build_packet("140", headers=headers, body=image_bytes)

        send_packet(tls_socket, request_packet)

        can_fit = None

        while True:
            packet = recv_packet(tls_socket)
            match packet.code:
                case "200":
                    text_logger.info("Server accepted BPCS capacity check request!")
                case "201":
                    text_logger.info(packet.headers["status"])
                case "204":
                    can_fit = bool(packet.headers["can-fit"])
                case "500":
                    text_logger.info(get_dissconnect_packet_line(packet))
                    break
                case _:
                    if packet.code[0] == "4" or packet.code[0] == "5":
                        text_logger.info(f"An error occurred: {get_dissconnect_packet_line(packet)}")
                        break

        text_logger.info(f"Disconnecting from server...")
        tls_socket.close()
        return can_fit

    except ConnectionError:
        text_logger.info("Server closed connection unexpectedly.")
    except ssl.SSLError as e:
        text_logger.info(f"There was en error regarding the TLS connection {e}")


def initiate_lsb_capacity_check_request(server_address: str, image_path: str, message_length: int,
                                        ecc_block_size: int, ecc_symbol_size: int, num_of_sacrificed_bits: int) -> bool:
    text_logger = multiprocessing.get_logger()
    try:
        tls_socket = new_server_connection(server_address)

        image_bytes = get_image_bytes(image_path)

        headers = {
            "ecc-block-size": str(ecc_block_size),
            "ecc-symbol-num": str(ecc_symbol_size),
            "number-of-sacrificed-bits": str(num_of_sacrificed_bits),
            "message-length": str(message_length),
        }
        request_packet = build_packet("141", headers=headers, body=image_bytes)

        send_packet(tls_socket, request_packet)

        can_fit = None

        while True:
            packet = recv_packet(tls_socket)
            match packet.code:
                case "200":
                    text_logger.info("Server accepted LSB capacity check request!")
                case "201":
                    text_logger.info(packet.headers["status"])
                case "204":
                    can_fit = bool(packet.headers["can-fit"])
                case "500":
                    text_logger.info(get_dissconnect_packet_line(packet))
                    break
                case _:
                    if packet.code[0] == "4" or packet.code[0] == "5":
                        text_logger.info(f"An error occurred: {get_dissconnect_packet_line(packet)}")
                        break

        text_logger.info(f"Disconnecting from server...")
        tls_socket.close()
        return can_fit

    except ConnectionError:
        text_logger.info("Server closed connection unexpectedly.")
    except ssl.SSLError as e:
        text_logger.info(f"There was en error regarding the TLS connection {e}")


def initiate_bitplane_slicing_request(server_address: str, image_path: str, output_directory_path: str):
    text_logger = multiprocessing.get_logger()
    try:
        tls_socket = new_server_connection(server_address)

        os.makedirs(output_directory_path, exist_ok=True)
        image_bytes = get_image_bytes(image_path)

        request_packet = build_packet("160", body=image_bytes)
        send_packet(tls_socket, request_packet)

        while True:
            packet = recv_packet(tls_socket)
            match packet.code:
                case "200":
                    text_logger.info("Server accepted BPCS capacity check request!")
                case "201":
                    text_logger.info(packet.headers["status"])
                case "260":
                    bitplane_slice = open(f"{output_directory_path}/{packet.headers["image-name"]}", "wb")
                    bitplane_slice.write(packet.body)
                case "500":
                    text_logger.info(get_dissconnect_packet_line(packet))
                    break
                case _:
                    if packet.code[0] == "4" or packet.code[0] == "5":
                        text_logger.info(f"An error occurred: {get_dissconnect_packet_line(packet)}")
                        break

        text_logger.info(f"Disconnecting from server...")
        tls_socket.close()

    except ConnectionError:
        text_logger.info("Server closed connection unexpectedly.")
    except ssl.SSLError as e:
        text_logger.info(f"There was en error regarding the TLS connection {e}")


def initiate_image_diff_calculation_request(server_address: str, image1_path: str, image2_path: str,
                                            exact_diff: bool, diff_image_path: str):
    text_logger = multiprocessing.get_logger()
    try:
        tls_socket = new_server_connection(server_address)

        image1_bytes = get_image_bytes(image1_path)
        image2_bytes = get_image_bytes(image2_path)

        request_packet = build_packet("161", headers={"show-exact-diff": str(int(exact_diff))}, body=image1_bytes)
        second_image_packet = build_packet("000", body=image2_bytes)

        send_packet(tls_socket, request_packet)
        send_packet(tls_socket, second_image_packet)

        while True:
            packet = recv_packet(tls_socket)
            match packet.code:
                case "200":
                    text_logger.info("Server accepted image difference calculation request!")
                case "201":
                    text_logger.info(packet.headers["status"])
                case "261":
                    text_logger.info("Received difference image from server!")
                    text_logger.info(f"Red channel max difference: {packet.headers["red-diff"]}")
                    text_logger.info(f"Green channel max difference: {packet.headers["green-diff"]}")
                    text_logger.info(f"Blue channel max difference: {packet.headers["blue-diff"]}")
                    open(diff_image_path, "wb").write(packet.body)
                case "500":
                    text_logger.info(get_dissconnect_packet_line(packet))
                    break
                case _:
                    if packet.code[0] == "4" or packet.code[0] == "5":
                        text_logger.info(f"An error occurred: {get_dissconnect_packet_line(packet)}")
                        break
        text_logger.info(f"Disconnecting from server...")
        tls_socket.close()

    except ConnectionError:
        text_logger.info("Server closed connection unexpectedly.")
    except ssl.SSLError as e:
        text_logger.info(f"There was en error regarding the TLS connection {e}")
