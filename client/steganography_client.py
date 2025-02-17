import os
import socket
import ssl
import time

from shared.communication_protocol.transmission import PORT, send_packet, recv_packet
from shared.communication_protocol.packet_analyzer import PacketInfo
from shared.communication_protocol.packet_builder import build_packet
from shared.utils import get_image_bytes, get_dissconnect_packet_line


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
        self.tls_context.load_verify_locations("shared/certificate_authority/ca-cert.pem")
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

            vessel_image_path = "client/test_assets/big2.png"
            stegged_image_path = "client/test_assets/out1.png"
            embedding_image_in_path = "client/test_assets/big2small.png"
            embedded_image_out_path = "client/test_assets/image_out.png"
            exact_diff_image_path = "client/test_assets/exact_diff.png"
            loose_diff_image_path = "client/test_assets/loose_diff.png"
            slices_output_dir = "client/test_assets/bitplane_slices"
            token_path = "client/token.bin"
            encryption_key = "Hello i am a keyyyyyyyyyyyyyyyyyyYYyyYYYYyyYYYYYY"
            ecc_block_size = 255
            ecc_symbol_num = 16
            bpcs_alpha = 0.3

            """
            self.initiate_bpcs_encodeing_request(vessel_image_path, stegged_image_path,
                                                 open(embedding_image_in_path, "rb").read(), token_path, encryption_key,
                                                 ecc_block_size, ecc_symbol_num, bpcs_alpha)
                                                 
            decoded_data = self.initiate_bpcs_decodeing_request(stegged_image_path, token_path)
            open(embedded_image_out_path, "wb").write(decoded_data)
            
            self.initiate_bpcs_capacity_check_request(vessel_image_path, 
                                                      len(open(embedding_image_in_path, "rb").read()), 
                                                      ecc_block_size, ecc_symbol_num, bpcs_alpha)
                                                      
            self.initiate_image_diff_calculation_request(vessel_image_path, stegged_image_path, True, 
                                                         exact_diff_image_path)

            self.initiate_image_diff_calculation_request(vessel_image_path, stegged_image_path, False, 
                                                         loose_diff_image_path)

            self.initiate_bitplane_slicing_request(exact_diff_image_path, slices_output_dir)
            """

        except ConnectionError:
            # server disconnected
            print("Server closed connection unexpectedly.")
        except ssl.SSLError as e:
            print(f"There was en error regarding the TLS connection {e}")
        finally:
            self.disconnect()

    def initiate_bpcs_encodeing_request(self, vessel_image_path: str, image_output_path: str, message_bytes: bytes,
                                        token_output_path: str, encryption_key: str, ecc_block_size: int,
                                        ecc_symbol_size: int, alpha: float) -> None:
        params_dict = {
            "encryption-key": encryption_key,
            "ecc-block-size": str(ecc_block_size),
            "ecc-symbol-num": str(ecc_symbol_size),
            "alpha": str(alpha),
        }

        vessel_image_bytes = get_image_bytes(vessel_image_path)

        request_packet = build_packet("100", headers=params_dict, body=vessel_image_bytes)
        message_packet = build_packet("000", body=message_bytes)

        send_packet(self.skt, request_packet)
        send_packet(self.skt, message_packet)

        while True:
            packet = recv_packet(self.skt)

            match packet.code:
                case "000":
                    print("Received BPCS token image from server!")
                    open(token_output_path, "wb").write(packet.body)
                case "200":
                    print("Server accepted BPCS encoding request!")
                case "201":
                    print(packet.headers["status"])
                case "202":
                    print("Recived BPCS encoded from server!")
                    open(image_output_path, "wb").write(packet.body)
                case "500":
                    print(get_dissconnect_packet_line(packet))
                    break
                case _:
                    if packet.code[0] == "4" or packet.code[0] == "5":
                        print(f"An error occurred: {get_dissconnect_packet_line(packet)}")
                        break

    def initiate_bpcs_decodeing_request(self, stegged_image_path: str, token_path: str) -> bytes:
        stegged_image_bytes = get_image_bytes(stegged_image_path)
        token_bytes = open(token_path, "rb").read()

        request_packet = build_packet("120", body=stegged_image_bytes)
        token_packet = build_packet("000", body=token_bytes)

        send_packet(self.skt, request_packet)
        send_packet(self.skt, token_packet)

        data = b""

        while True:
            packet = recv_packet(self.skt)
            match packet.code:
                case "200":
                    print("Server accepted BPCS decoding request!")
                case "201":
                    print(packet.headers["status"])
                case "203":
                    print("Recived decoded data from server!")
                    data = packet.body
                case "500":
                    print(get_dissconnect_packet_line(packet))
                    break
                case _:
                    if packet.code[0] == "4" or packet.code[0] == "5":
                        print(f"An error occurred: {get_dissconnect_packet_line(packet)}")
                        break
        return data

    def initiate_bpcs_capacity_check_request(self, image_path: str, message_length: int, ecc_block_size: int,
                                             ecc_symbol_size: int, alpha: float) -> bool:
        image_bytes = get_image_bytes(image_path)

        headers = {
            "ecc-block-size": str(ecc_block_size),
            "ecc-symbol-num": str(ecc_symbol_size),
            "alpha": str(alpha),
            "message-length": str(message_length),
        }
        request_packet = build_packet("140", headers=headers, body=image_bytes)

        send_packet(self.skt, request_packet)

        can_fit = None

        while True:
            packet = recv_packet(self.skt)
            match packet.code:
                case "200":
                    print("Server accepted BPCS capacity check request!")
                case "201":
                    print(packet.headers["status"])
                case "204":
                    can_fit = bool(packet.headers["can-fit"])
                case "500":
                    print(get_dissconnect_packet_line(packet))
                    break
                case _:
                    if packet.code[0] == "4" or packet.code[0] == "5":
                        print(f"An error occurred: {get_dissconnect_packet_line(packet)}")
                        break

        return can_fit

    def initiate_bitplane_slicing_request(self, image_path: str, output_directory_path: str):
        os.makedirs(output_directory_path, exist_ok=True)
        image_bytes = get_image_bytes(image_path)

        request_packet = build_packet("160", body=image_bytes)
        send_packet(self.skt, request_packet)

        while True:
            packet = recv_packet(self.skt)
            match packet.code:
                case "200":
                    print("Server accepted BPCS capacity check request!")
                case "201":
                    print(packet.headers["status"])
                case "260":
                    bitplane_slice = open(f"{output_directory_path}/{packet.headers["image-name"]}", "wb")
                    bitplane_slice.write(packet.body)
                case "500":
                    print(get_dissconnect_packet_line(packet))
                    break
                case _:
                    if packet.code[0] == "4" or packet.code[0] == "5":
                        print(f"An error occurred: {get_dissconnect_packet_line(packet)}")
                        break

    def initiate_image_diff_calculation_request(self, image1_path: str, image2_path: str, exact_diff: bool,
                                                diff_image_path: str):
        image1_bytes = get_image_bytes(image1_path)
        image2_bytes = get_image_bytes(image2_path)

        request_packet = build_packet("161", headers={"show-exact-diff": str(int(exact_diff))}, body=image1_bytes)
        second_image_packet = build_packet("000", body=image2_bytes)

        send_packet(self.skt, request_packet)
        send_packet(self.skt, second_image_packet)

        while True:
            packet = recv_packet(self.skt)
            match packet.code:
                case "200":
                    print("Server accepted image difference calculation request!")
                case "201":
                    print(packet.headers["status"])
                case "261":
                    print("Recived difference image from server!")
                    print(f"Red channel max difference: {packet.headers["red-diff"]}")
                    print(f"Green channel max difference: {packet.headers["green-diff"]}")
                    print(f"Blue channel max difference: {packet.headers["blue-diff"]}")
                    open(diff_image_path, "wb").write(packet.body)
                case "500":
                    print(get_dissconnect_packet_line(packet))
                    break
                case _:
                    if packet.code[0] == "4" or packet.code[0] == "5":
                        print(f"An error occurred: {get_dissconnect_packet_line(packet)}")
                        break

    def disconnect(self) -> None:
        """
        Disconnects from the server; closes the socket
        """
        print(f"Disconnecting from server...")
        self.skt.close()
