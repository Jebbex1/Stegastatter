import logging
import multiprocessing
import threading
from enum import IntEnum
from PySide6.QtGui import QTextCursor, QPixmap
from PySide6.QtWidgets import QFileDialog, QWidget, QVBoxLayout, QMainWindow, QPushButton, QTextEdit, QCheckBox

from client.client_connection import ClientConnection
from client.gui.gui_errors import MissingParametersError, InvalidParametersError
from client.gui.gui_utils import get_form_field_text
from client.gui.params_validator import validate_lsb_params, validate_bpcs_params, validate_ecc_params
from client.gui.textedit_logger import LoggerOperationsHandler
from client.gui.ui_wigdet_generator import generate_custom_button, generate_encryption_key_field_widget, \
    generate_lsb_params_widget, generate_bpcs_params_widget, generate_ecc_params_widget
from client.gui.ui_loader import load_ui
from shared.communication_protocol.constants import CHARSET, MAX_FIELD_SIZE, MAX_FILE_SIZE

IMAGE_FILTER = "Image Files (*.png *.bmp)"
ANY_FILE_FILTER = "All Files (*.*)"
BIN_FILE_FILTER = "Binary Files (*.bin)"

VESSEL_IMAGE_INPUT_LABEL = "Select Vessel Image Input File"
STEGGED_IMAGE_INPUT_LABEL = "Select Stegged Image Input File"
STEGGED_IMAGE_OUTPUT_LABEL = "Select Stegged Image Output File"
MESSAGE_INPUT_FILE_LABEL = "Select Message Input File"
MESSAGE_OUTPUT_FILE_LABEL = "Select Message Output File"
TOKEN_INPUT_FILE_LABEL = "Select Token Input File"
TOKEN_OUTPUT_FILE_LABEL = "Select Token Output File"

USED_BUTTON_COLOR = "#3535A3"
NORMAL_TEXT_COLOR = "#FFFFFF"
WARNING_TEXT_COLOR = "#C72D2D"

SERVER_ADDRESS = "127.0.0.1"


class AlgorithmProfiles(IntEnum):
    LSB_EMBED = 1
    BPCS_EMBED = 2
    GENERIC_EXTRACT = 3
    LSB_MAX_CAPACITY = 4
    BPCS_MAX_CAPACITY = 5
    BIT_PLANE_SLICING = 6
    IMAGE_DIFF = 7


def validate_header_field_length(field: str):
    if len(field.encode(CHARSET)) > MAX_FIELD_SIZE:
        raise InvalidParametersError(f"The field content '{field}' is too long. Maximum size "
                                     f"is {len((b'_' * MAX_FIELD_SIZE).decode(CHARSET))}.")


class StegastatterApplication:
    def __init__(self):
        super().__init__()
        self.selected_paths_set = set()
        self.selected_vessel_input_path = None
        self.selected_stegged_input_path = None
        self.selected_stegged_output_path = None
        self.selected_message_input_path = None
        self.selected_message_output_path = None
        self.selected_token_input_path = None
        self.selected_token_output_path = None
        self.selected_image_diff_output_path = None
        self.selected_image_diff_input_1 = None
        self.selected_image_diff_input_2 = None
        self.selected_bit_plane_slicing_output_folder_path = None
        self.selected_algorithm_profile = 0

        self.main_window: QMainWindow = load_ui("client/gui/ui_files/main_window.ui")
        self.main_window.setWindowIcon(QPixmap("client/gui/assets/icon64.png"))
        self.main_window.setWindowTitle("Stegastatter Client")
        self.start_button: QPushButton = self.create_linked_start_button()

        self.status_logs: QTextEdit = load_ui("client/gui/ui_files/status_log.ui")

        status_logger = multiprocessing.get_logger()
        status_logger.setLevel(logging.DEBUG)
        self.handler = LoggerOperationsHandler(self.status_logs, self.start_button)

        status_logger.addHandler(self.handler)
        status_logger.addFilter(self.update_status)

        self.connect_actions()
        self.main_window.show()

        self.client_connection: ClientConnection | None = None
        self.communication_thread: threading.Thread | None = None

    def safe_close(self):
        if self.client_connection is not None:
            self.client_connection.initiate_terminatation_protocol()

    def update_status(self, record: logging.LogRecord):
        match record.levelname:
            case "INFO":
                white_text = f"<span style=\" color:{NORMAL_TEXT_COLOR};\" >{record.getMessage()}</span>"
                self.handler.bridge.log.emit(white_text)
            case "WARN" | "WARNING":
                red_text = f"<span style=\" color:{WARNING_TEXT_COLOR};\" >{record.getMessage()}</span>"
                self.handler.bridge.log.emit(red_text)
            case "DEBUG":
                self.handler.bridge.toggle_button.emit(False)

        self.handler.bridge.move.emit(QTextCursor.MoveOperation.End)
        return True

    def reset_selected_paths(self):
        self.selected_paths_set = set()
        self.selected_vessel_input_path = None
        self.selected_stegged_input_path = None
        self.selected_stegged_output_path = None
        self.selected_message_input_path = None
        self.selected_message_output_path = None
        self.selected_token_input_path = None
        self.selected_token_output_path = None
        self.selected_image_diff_output_path = None
        self.selected_image_diff_input_1 = None
        self.selected_image_diff_input_2 = None
        self.selected_bit_plane_slicing_output_folder_path = None

    def connect_actions(self):
        self.main_window.action_embed_lsb.triggered.connect(self.use_lsb_embedding_widget)
        self.main_window.action_embed_bpcs.triggered.connect(self.use_bpcs_embedding_widget)
        self.main_window.action_extract_generic.triggered.connect(self.use_extracting_widget)
        self.main_window.action_capacity_max_calculation_lsb.triggered.connect(self.use_lsb_max_capacity_widget)
        self.main_window.action_capacity_max_calculation_bpcs.triggered.connect(self.use_bpcs_max_capacity_widget)
        self.main_window.action_slice_image_bit_planes.triggered.connect(self.use_bit_plane_slicing_widget)
        self.main_window.action_get_diff.triggered.connect(self.use_image_diff_widget)

    def validate_file_path(self, path: str, validate_size: bool):
        if path in self.selected_paths_set:
            raise InvalidParametersError(f"Path '{path}' is already selected, please select another one.")

        if path == "":
            raise MissingParametersError(f"A path is empty, please select one.")

        if validate_size:
            if len(open(path, "rb").read()) > MAX_FILE_SIZE:
                raise InvalidParametersError(f"File at path '{path}' is to large. Please choose a file that does not "
                                             f"exceed {MAX_FILE_SIZE} bytes.")

    def start_button_clicked(self, checked: bool):
        if checked:
            self.status_logs.clear()
            self.start_button.setText("Stop")
            self.initiate_steganography_action()
        else:
            if self.client_connection is not None:
                self.client_connection.initiate_terminatation_protocol()
            self.start_button.setText("Start")

    def initiate_steganography_action(self):
        self.client_connection = ClientConnection(SERVER_ADDRESS, threading.Lock())
        try:
            match self.selected_algorithm_profile:
                case AlgorithmProfiles.LSB_EMBED:
                    self.start_lsb_embed()
                case AlgorithmProfiles.BPCS_EMBED:
                    self.start_bpcs_embed()
                case AlgorithmProfiles.GENERIC_EXTRACT:
                    self.start_generic_extract()
                case AlgorithmProfiles.LSB_MAX_CAPACITY:
                    self.start_lsb_max_capacity()
                case AlgorithmProfiles.BPCS_MAX_CAPACITY:
                    self.start_bpcs_max_capacity()
                case AlgorithmProfiles.BIT_PLANE_SLICING:
                    self.start_bit_plane_slicing()
                case AlgorithmProfiles.IMAGE_DIFF:
                    self.start_image_diff()

        except (InvalidParametersError, MissingParametersError) as e:
            multiprocessing.get_logger().warn(e.__str__())
            self.start_button.setChecked(False)
            self.client_connection = None

    def update_menu_widget(self, widget: QWidget):
        self.reset_selected_paths()
        widget.layout().addStretch()

        self.start_button.setChecked(False)
        widget.layout().addWidget(self.start_button)

        self.status_logs.clear()
        widget.layout().addWidget(self.status_logs)

        self.communication_thread = None

        self.main_window.setMinimumSize(widget.minimumSize())
        self.main_window.setCentralWidget(widget)

    def prompt_get_vessel_input_path(self, button: QPushButton):
        self.selected_paths_set.discard(self.selected_vessel_input_path)
        path = QFileDialog.getOpenFileName(self.main_window,
                                           "Select an existing image to use as a Vessel Image",
                                           filter=IMAGE_FILTER)[0]
        
        try:
            self.validate_file_path(path, True)
        except (InvalidParametersError, MissingParametersError) as e:
            multiprocessing.get_logger().warn(e.__str__())
            return

        self.selected_vessel_input_path = path
        self.selected_paths_set.add(self.selected_vessel_input_path)

        button.setStyleSheet(f"background-color: {USED_BUTTON_COLOR};")

    def prompt_get_stegged_input_path(self, button: QPushButton):
        self.selected_paths_set.discard(self.selected_stegged_input_path)
        path = QFileDialog.getOpenFileName(self.main_window,
                                           "Select an existing image to extract data from",
                                           filter=IMAGE_FILTER)[0]

        try:
            self.validate_file_path(path, True)
        except (InvalidParametersError, MissingParametersError) as e:
            multiprocessing.get_logger().warn(e.__str__())
            return

        self.selected_stegged_input_path = path
        self.selected_paths_set.add(self.selected_stegged_input_path)

        button.setStyleSheet(f"background-color: {USED_BUTTON_COLOR};")

    def prompt_get_stegged_output_path(self, button: QPushButton):
        self.selected_paths_set.discard(self.selected_stegged_output_path)
        path = QFileDialog.getSaveFileName(self.main_window,
                                           "Select where to save the Stegged Image",
                                           filter=IMAGE_FILTER)[0]

        try:
            self.validate_file_path(path, False)
        except (InvalidParametersError, MissingParametersError) as e:
            multiprocessing.get_logger().warn(e.__str__())
            return

        self.selected_stegged_output_path = path
        self.selected_paths_set.add(self.selected_stegged_output_path)

        button.setStyleSheet(f"background-color: {USED_BUTTON_COLOR};")

    def prompt_get_message_input_path(self, button: QPushButton):
        self.selected_paths_set.discard(self.selected_message_input_path)
        path = QFileDialog.getOpenFileName(self.main_window,
                                           "Select a file to embed into an image",
                                           filter=ANY_FILE_FILTER)[0]

        try:
            self.validate_file_path(path, True)
        except (InvalidParametersError, MissingParametersError) as e:
            multiprocessing.get_logger().warn(e.__str__())
            return

        self.selected_message_input_path = path
        self.selected_paths_set.add(self.selected_message_input_path)

        button.setStyleSheet(f"background-color: {USED_BUTTON_COLOR};")

    def prompt_get_message_output_path(self, button: QPushButton):
        self.selected_paths_set.discard(self.selected_message_output_path)
        path = QFileDialog.getSaveFileName(self.main_window,
                                           "Select where to save the extracted data",
                                           filter=ANY_FILE_FILTER)[0]

        try:
            self.validate_file_path(path, False)
        except (InvalidParametersError, MissingParametersError) as e:
            multiprocessing.get_logger().warn(e.__str__())
            return

        self.selected_message_output_path = path
        self.selected_paths_set.add(self.selected_message_output_path)

        button.setStyleSheet(f"background-color: {USED_BUTTON_COLOR};")

    def prompt_get_token_input_path(self, button: QPushButton):
        self.selected_paths_set.discard(self.selected_token_input_path)
        path = QFileDialog.getOpenFileName(self.main_window,
                                           "Select the token that contains the extracting algorithm parameters "
                                           "for this image",
                                           filter=BIN_FILE_FILTER)[0]

        try:
            self.validate_file_path(path, True)
        except (InvalidParametersError, MissingParametersError) as e:
            multiprocessing.get_logger().warn(e.__str__())
            return

        self.selected_token_input_path = path
        self.selected_paths_set.add(self.selected_token_input_path)

        button.setStyleSheet(f"background-color: {USED_BUTTON_COLOR};")

    def prompt_get_token_output_path(self, button: QPushButton):
        self.selected_paths_set.discard(self.selected_token_output_path)
        path = QFileDialog.getSaveFileName(self.main_window,
                                           "Select where to save the token that contains all the "
                                           "algorithm parameters",
                                           filter=BIN_FILE_FILTER)[0]

        try:
            self.validate_file_path(path, False)
        except (InvalidParametersError, MissingParametersError) as e:
            multiprocessing.get_logger().warn(e.__str__())
            return

        self.selected_token_output_path = path
        self.selected_paths_set.add(self.selected_token_output_path)

        button.setStyleSheet(f"background-color: {USED_BUTTON_COLOR};")

    def prompt_get_image_diff_input_1_path(self, button: QPushButton):
        self.selected_paths_set.discard(self.selected_image_diff_input_1)
        path = QFileDialog.getOpenFileName(self.main_window,
                                           "Select the first image to compare",
                                           filter=IMAGE_FILTER)[0]

        try:
            self.validate_file_path(path, True)
        except (InvalidParametersError, MissingParametersError) as e:
            multiprocessing.get_logger().warn(e.__str__())
            return

        self.selected_image_diff_input_1 = path
        self.selected_paths_set.add(self.selected_image_diff_input_1)

        button.setStyleSheet(f"background-color: {USED_BUTTON_COLOR};")

    def prompt_get_image_diff_input_2_path(self, button: QPushButton):
        self.selected_paths_set.discard(self.selected_image_diff_input_2)
        path = QFileDialog.getOpenFileName(self.main_window,
                                           "Select the second image to compare",
                                           filter=IMAGE_FILTER)[0]

        try:
            self.validate_file_path(path, True)
        except (InvalidParametersError, MissingParametersError) as e:
            multiprocessing.get_logger().warn(e.__str__())
            return

        self.selected_image_diff_input_2 = path
        self.selected_paths_set.add(self.selected_image_diff_input_2)

        button.setStyleSheet(f"background-color: {USED_BUTTON_COLOR};")

    def prompt_get_image_diff_output_path(self, button: QPushButton):
        self.selected_paths_set.discard(self.selected_image_diff_output_path)
        path = QFileDialog.getSaveFileName(self.main_window,
                                           "Select where to save the image that contains the diffrence between "
                                           "the provided images",
                                           filter=IMAGE_FILTER)[0]

        try:
            self.validate_file_path(path, False)
        except (InvalidParametersError, MissingParametersError) as e:
            multiprocessing.get_logger().warn(e.__str__())
            return

        self.selected_image_diff_output_path = path
        self.selected_paths_set.add(self.selected_image_diff_output_path)

        button.setStyleSheet(f"background-color: {USED_BUTTON_COLOR};")

    def prompt_get_bit_plane_slicing_output_folder_path(self, button: QPushButton):
        self.selected_paths_set.discard(self.selected_bit_plane_slicing_output_folder_path)
        path = QFileDialog.getExistingDirectory(self.main_window,
                                                "Select where to save the sliced bit planes of the "
                                                "provided image")

        try:
            self.validate_file_path(path, False)
        except (InvalidParametersError, MissingParametersError) as e:
            multiprocessing.get_logger().warn(e.__str__())
            return

        self.selected_bit_plane_slicing_output_folder_path = path
        self.selected_paths_set.add(self.selected_bit_plane_slicing_output_folder_path)

        button.setStyleSheet(f"background-color: {USED_BUTTON_COLOR};")

    def create_linked_embedding_widget(self) -> QWidget:
        """
        For embedding we need:
        1. vessel image input button
        2. stegged image output button
        3. message file input button
        4. token file output button
        5. encryption key field
        6. LSB/BPCS parameters
        7. ECC parameters
        """
        widget = QWidget()
        widget.setLayout(QVBoxLayout())
        layout = widget.layout()

        layout.addWidget(generate_custom_button(VESSEL_IMAGE_INPUT_LABEL, self.prompt_get_vessel_input_path))
        layout.addWidget(generate_custom_button(STEGGED_IMAGE_OUTPUT_LABEL, self.prompt_get_stegged_output_path))
        layout.addWidget(generate_custom_button(MESSAGE_INPUT_FILE_LABEL, self.prompt_get_message_input_path))
        layout.addWidget(generate_custom_button(TOKEN_OUTPUT_FILE_LABEL, self.prompt_get_token_output_path))
        layout.addWidget(generate_encryption_key_field_widget())

        match self.selected_algorithm_profile:
            case AlgorithmProfiles.LSB_EMBED:
                layout.addWidget(generate_lsb_params_widget())
            case AlgorithmProfiles.BPCS_EMBED:
                layout.addWidget(generate_bpcs_params_widget())

        layout.addWidget(generate_ecc_params_widget())

        return widget

    def create_linked_extracting_widget(self) -> QWidget:
        widget = QWidget()
        widget.setLayout(QVBoxLayout())
        layout = widget.layout()

        layout.addWidget(generate_custom_button(STEGGED_IMAGE_INPUT_LABEL, self.prompt_get_stegged_input_path))
        layout.addWidget(generate_custom_button(MESSAGE_OUTPUT_FILE_LABEL, self.prompt_get_message_output_path))
        layout.addWidget(generate_custom_button(TOKEN_INPUT_FILE_LABEL, self.prompt_get_token_input_path))

        return widget

    def create_linked_max_capacity_widget(self) -> QWidget:
        widget = QWidget()
        widget.setLayout(QVBoxLayout())
        layout = widget.layout()

        layout.addWidget(generate_custom_button(VESSEL_IMAGE_INPUT_LABEL, self.prompt_get_vessel_input_path))

        match self.selected_algorithm_profile:
            case AlgorithmProfiles.LSB_MAX_CAPACITY:
                layout.addWidget(generate_lsb_params_widget())
            case AlgorithmProfiles.BPCS_MAX_CAPACITY:
                layout.addWidget(generate_bpcs_params_widget())

        layout.addWidget(generate_ecc_params_widget())

        return widget

    def create_linked_bit_plane_slicing_widget(self) -> QWidget:
        widget = QWidget()
        widget.setLayout(QVBoxLayout())
        layout = widget.layout()

        layout.addWidget(generate_custom_button("Select Image Input File", self.prompt_get_vessel_input_path))
        layout.addWidget(generate_custom_button("Select Image Output Folder",
                                                self.prompt_get_bit_plane_slicing_output_folder_path))

        return widget

    def create_linked_image_diff_widget(self) -> QWidget:
        widget = QWidget()
        widget.setLayout(QVBoxLayout())
        layout = widget.layout()

        layout.addWidget(generate_custom_button("Select 1st Image Input File", self.prompt_get_image_diff_input_1_path))
        layout.addWidget(generate_custom_button("Select 2nd Image Input File", self.prompt_get_image_diff_input_2_path))
        layout.addWidget(generate_custom_button("Select Image Diffrence Output File",
                                                self.prompt_get_image_diff_output_path))
        checkbox = QCheckBox("Show exact difference")
        checkbox.setChecked(True)
        layout.addWidget(checkbox)

        return widget

    def create_linked_start_button(self) -> QPushButton:
        dialog_button = QPushButton("Start")
        dialog_button.setCheckable(True)
        dialog_button.toggled.connect(self.start_button_clicked)

        return dialog_button

    def use_lsb_embedding_widget(self):
        self.selected_algorithm_profile = AlgorithmProfiles.LSB_EMBED
        widget = self.create_linked_embedding_widget()
        self.update_menu_widget(widget)

    def use_bpcs_embedding_widget(self):
        self.selected_algorithm_profile = AlgorithmProfiles.BPCS_EMBED
        widget = self.create_linked_embedding_widget()
        self.update_menu_widget(widget)

    def use_extracting_widget(self):
        self.selected_algorithm_profile = AlgorithmProfiles.GENERIC_EXTRACT
        widget = self.create_linked_extracting_widget()
        self.update_menu_widget(widget)

    def use_lsb_max_capacity_widget(self):
        self.selected_algorithm_profile = AlgorithmProfiles.LSB_MAX_CAPACITY
        widget = self.create_linked_max_capacity_widget()
        self.update_menu_widget(widget)

    def use_bpcs_max_capacity_widget(self):
        self.selected_algorithm_profile = AlgorithmProfiles.BPCS_MAX_CAPACITY
        widget = self.create_linked_max_capacity_widget()
        self.update_menu_widget(widget)

    def use_bit_plane_slicing_widget(self):
        self.selected_algorithm_profile = AlgorithmProfiles.BIT_PLANE_SLICING
        widget = self.create_linked_bit_plane_slicing_widget()
        self.update_menu_widget(widget)

    def use_image_diff_widget(self):
        self.selected_algorithm_profile = AlgorithmProfiles.IMAGE_DIFF
        widget = self.create_linked_image_diff_widget()
        self.update_menu_widget(widget)

    def get_central_widget_item_at(self, index: int):
        return self.main_window.centralWidget().layout().itemAt(index)

    def get_form_field_text_at_group_box_at(self, group_box_index: int, form_field_index: int):
        layout_item = self.get_central_widget_item_at(group_box_index).widget().layout().itemAt(form_field_index)
        return get_form_field_text(layout_item)

    def get_encryption_key_at(self, index: int):
        return get_form_field_text(self.get_central_widget_item_at(index).widget().layout().itemAt(0))

    def get_ecc_params_at(self, group_box_index: int) -> tuple[str, str]:
        block_size = self.get_form_field_text_at_group_box_at(group_box_index, 0)
        symbol_num = self.get_form_field_text_at_group_box_at(group_box_index, 1)
        return block_size, symbol_num

    def get_embedding_params(self) -> tuple[str, str, str]:
        encryption_key = self.get_encryption_key_at(4)
        block_size, symbol_num = self.get_ecc_params_at(6)
        return encryption_key, block_size, symbol_num

    def validate_embed_paths(self):
        if self.selected_vessel_input_path is None:
            raise MissingParametersError("A vessel image input path is required.")
        if self.selected_stegged_output_path is None:
            raise MissingParametersError("A stegged image output path is required.")
        if self.selected_message_input_path is None:
            raise MissingParametersError("A message file input path is required.")
        if self.selected_token_output_path is None:
            raise MissingParametersError("A token file output path is required.")

    def validate_extract_paths(self):
        if self.selected_stegged_input_path is None:
            raise MissingParametersError("A stegged image input path is required.")
        if self.selected_message_output_path is None:
            raise MissingParametersError("A message file output path is required.")
        if self.selected_token_input_path is None:
            raise MissingParametersError("A token file input path is required.")

    def validate_max_capacity_paths(self):
        if self.selected_vessel_input_path is None:
            raise MissingParametersError("A vessel image input path is required.")

    def validate_bit_plane_slicing_paths(self):
        if self.selected_vessel_input_path is None:
            raise MissingParametersError("An image input path is required.")
        if self.selected_bit_plane_slicing_output_folder_path is None:
            raise MissingParametersError("A sliced bit planes output folder path is required.")

    def validate_image_diff_paths(self):
        if self.selected_image_diff_input_1 is None:
            raise MissingParametersError("A 1st image input path for image diff is required.")
        if self.selected_image_diff_input_2 is None:
            raise MissingParametersError("A 2nd image input path for image diff is required.")
        if self.selected_image_diff_output_path is None:
            raise MissingParametersError("An image diff output path is required.")

    def start_lsb_embed(self):
        self.validate_embed_paths()
        encryption_key, block_size, symbol_num = self.get_embedding_params()
        num_of_sacrificed_bits = self.get_form_field_text_at_group_box_at(5, 0)

        validate_header_field_length(encryption_key)
        validate_header_field_length(block_size)
        validate_header_field_length(symbol_num)
        validate_header_field_length(num_of_sacrificed_bits)

        validate_lsb_params(num_of_sacrificed_bits)
        validate_ecc_params(block_size, symbol_num)

        block_size = int(block_size)
        symbol_num = int(symbol_num)
        num_of_sacrificed_bits = int(num_of_sacrificed_bits)

        self.communication_thread = threading.Thread(target=self.client_connection.initiate_lsb_embedding_request,
                                                     args=(self.selected_vessel_input_path,
                                                           self.selected_stegged_output_path,
                                                           self.selected_message_input_path,
                                                           self.selected_token_output_path,
                                                           encryption_key, block_size,
                                                           symbol_num, num_of_sacrificed_bits))
        self.communication_thread.start()

    def start_bpcs_embed(self):
        self.validate_embed_paths()
        encryption_key, block_size, symbol_num = self.get_embedding_params()
        min_alpha = self.get_form_field_text_at_group_box_at(5, 0)

        validate_header_field_length(encryption_key)
        validate_header_field_length(block_size)
        validate_header_field_length(symbol_num)
        validate_header_field_length(min_alpha)

        validate_bpcs_params(min_alpha)
        validate_ecc_params(block_size, symbol_num)

        block_size = int(block_size)
        symbol_num = int(symbol_num)
        min_alpha = float(min_alpha)

        self.communication_thread = threading.Thread(target=self.client_connection.initiate_bpcs_embedding_request,
                                                     args=(self.selected_vessel_input_path,
                                                           self.selected_stegged_output_path,
                                                           self.selected_message_input_path,
                                                           self.selected_token_output_path,
                                                           encryption_key, block_size,
                                                           symbol_num, min_alpha))
        self.communication_thread.start()

    def start_generic_extract(self):
        self.validate_extract_paths()

        self.communication_thread = threading.Thread(target=self.client_connection.initiate_extracting_request,
                                                     args=(self.selected_stegged_input_path,
                                                           self.selected_message_output_path,
                                                           self.selected_token_input_path))
        self.communication_thread.start()

    def start_lsb_max_capacity(self):
        self.validate_max_capacity_paths()
        block_size, symbol_num = self.get_ecc_params_at(2)
        num_of_sacrificed_bits = self.get_form_field_text_at_group_box_at(1, 0)

        validate_header_field_length(block_size)
        validate_header_field_length(symbol_num)
        validate_header_field_length(num_of_sacrificed_bits)

        validate_lsb_params(num_of_sacrificed_bits)
        validate_ecc_params(block_size, symbol_num)

        block_size = int(block_size)
        symbol_num = int(symbol_num)
        num_of_sacrificed_bits = int(num_of_sacrificed_bits)

        self.communication_thread = threading.Thread(target=self.client_connection.initiate_lsb_max_capacity_request,
                                                     args=(self.selected_vessel_input_path,
                                                           block_size, symbol_num, num_of_sacrificed_bits))
        self.communication_thread.start()

    def start_bpcs_max_capacity(self):
        self.validate_max_capacity_paths()
        block_size, symbol_num = self.get_ecc_params_at(2)
        min_alpha = self.get_form_field_text_at_group_box_at(1, 0)

        validate_header_field_length(block_size)
        validate_header_field_length(symbol_num)
        validate_header_field_length(min_alpha)

        validate_bpcs_params(min_alpha)
        validate_ecc_params(block_size, symbol_num)

        block_size = int(block_size)
        symbol_num = int(symbol_num)
        min_alpha = float(min_alpha)

        self.communication_thread = threading.Thread(target=self.client_connection.initiate_bpcs_max_capacity_request,
                                                     args=(self.selected_vessel_input_path,
                                                           block_size, symbol_num, min_alpha))
        self.communication_thread.start()

    def start_bit_plane_slicing(self):
        self.validate_bit_plane_slicing_paths()

        self.communication_thread = threading.Thread(target=self.client_connection.initiate_bitplane_slicing_request,
                                                     args=(self.selected_vessel_input_path,
                                                           self.selected_bit_plane_slicing_output_folder_path))
        self.communication_thread.start()

    def start_image_diff(self):
        self.validate_image_diff_paths()
        exact_diff = self.get_central_widget_item_at(3).widget().isChecked()

        self.communication_thread = threading.Thread(target=self.client_connection.initiate_image_diff_request,
                                                     args=(self.selected_image_diff_input_1,
                                                           self.selected_image_diff_input_2, exact_diff,
                                                           self.selected_image_diff_output_path))
        self.communication_thread.start()
