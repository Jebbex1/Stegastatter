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

            """self.initiate_bpcs_encodeing_request("test_assets/big2.png", "client/out1.png",
                                                 open("test_assets/message.txt", "rb").read(), "client/token.bin",
                                                 "KEYYY", 255, 16, 0.2)

            data = self.initiate_bpcs_decodeing_request("client/out1.png", "client/token.bin")
            open("client/data.txt", "wb").write(data)"""

        except ConnectionError:
            # server disconnected
            print("Server closed connection")
            self.disconnect()
        except ssl.SSLError as e:
            print(f"There was en error regarding the TLS connection {e}")

    def initiate_bpcs_encodeing_request(self, vessel_image_path: str, image_output_path: str, message_bytes: bytes,
                                        token_output_path: str, encryption_key: str, ecc_block_size: int,
                                        ecc_symbol_size: int, alpha: float) -> None:
        params_dict = {
                       "encryption-key": encryption_key,
                       "ecc-block-size": str(ecc_block_size),
                       "ecc-symbol-num": str(ecc_symbol_size),
                       "alpha": str(alpha),
                       }

        vessel_image_bytes = open(vessel_image_path, "rb").read()

        request_packet = build_packet("100", headers=params_dict, body=message_bytes)
        vessel_upload_packet = build_packet("000", body=vessel_image_bytes)

        send_packet(self.skt, request_packet)
        send_packet(self.skt, vessel_upload_packet)

        while True:
            packet = recv_packet(self.skt)

            match packet.code.decode():
                case "201":
                    print(packet.headers[b"status"].decode())
                case "202":
                    print("Recived BPCS token from server!")
                    open(token_output_path, "wb").write(packet.body)
                case "000":
                    print("Received BPCS encoded image from server!")
                    open(image_output_path, "wb").write(packet.body)
                case "500":
                    break
                case _:
                    if packet.code.decode()[0] == "4" or packet.code.decode()[0] == "5":
                        print(f"An error occurred: {packet.desc.decode()}")

    def initiate_bpcs_decodeing_request(self, stegged_image_path: str, token_path: str) -> bytes:
        stegged_image_bytes = open(stegged_image_path, "rb").read()
        token_bytes = open(token_path, "rb").read()

        request_packet = build_packet("150", body=token_bytes)
        stegged_upload_packet = build_packet("000", body=stegged_image_bytes)

        send_packet(self.skt, request_packet)
        send_packet(self.skt, stegged_upload_packet)

        data = b""

        while True:
            packet = recv_packet(self.skt)
            match packet.code.decode():
                case "201":
                    print(packet.headers[b"status"].decode())
                case "203":
                    print("Recived decoded data from server!")
                    data = packet.body
                case "500":
                    break
                case _:
                    if packet.code.decode()[0] == "4" or packet.code.decode()[0] == "5":
                        print(f"An error occurred: {packet.desc.decode()}")
        return data

    def disconnect(self) -> None:
        """
        Disconnects from the server; closes the socket
        """
        print(f"Disconnecting from server")
        self.skt.close()
