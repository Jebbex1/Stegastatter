import logging
import sys
import threading
import multiprocessing

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QApplication, QPushButton, QGroupBox

from client.client_connection import (initiate_bpcs_encoding_request,
                                      initiate_bpcs_decoding_request, initiate_bitplane_slicing_request,
                                      initiate_bpcs_capacity_check_request, initiate_image_diff_calculation_request,
                                      initiate_lsb_encoding_request, initiate_lsb_decoding_request,
                                      initiate_lsb_capacity_check_request)
from client.gui.log_widget import LogWidget
from client.gui.main_window import MainWindow


def start():
    server_address = "127.0.0.1"
    vessel_image_path = "client/test_assets/big2.png"
    stegged_image_path = "client/test_assets/out1.png"
    message_in_path = "client/test_assets/message.txt"
    message_out_path = "client/test_assets/message_out.txt"
    exact_diff_image_path = "client/test_assets/exact_diff.png"
    loose_diff_image_path = "client/test_assets/loose_diff.png"
    slices_output_dir = "client/test_assets/bitplane_slices"
    token_path = "client/token.bin"
    encryption_key = "Hello i am a keyyyyyyyyyyyyyyyyyyYYyyYYy"
    ecc_block_size = 255
    ecc_symbol_num = 32
    lsb_number_of_sacrificed_bits = 2

    print("b")
    initiate_lsb_encoding_request(server_address, vessel_image_path, stegged_image_path,
                                  open(message_in_path, "rb").read(), token_path, encryption_key,
                                  ecc_block_size, ecc_symbol_num, lsb_number_of_sacrificed_bits)
    print("c")
    decoded_data = initiate_lsb_decoding_request(server_address, stegged_image_path, token_path)
    open(message_out_path, "wb").write(decoded_data)
    print("d")


"""    initiate_image_diff_calculation_request(server_address, vessel_image_path, stegged_image_path, True,
                                            exact_diff_image_path)

    initiate_image_diff_calculation_request(server_address, vessel_image_path, stegged_image_path, False,
                                            loose_diff_image_path)

    initiate_bitplane_slicing_request(server_address, exact_diff_image_path, slices_output_dir)"""

if __name__ == '__main__':
    """    def start_1():
        threading.Thread(target=start).start()


    app = QApplication(sys.argv)

    window = MainWindow("Test")

    trigger = QPushButton()
    trigger.clicked.connect(start_1)

    window.setCentralWidget(trigger)

    window.show()

    sys.exit(app.exec())"""

    start()
