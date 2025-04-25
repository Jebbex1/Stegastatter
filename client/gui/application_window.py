from enum import IntEnum

from PySide6.QtWidgets import QFileDialog, QWidget, QVBoxLayout, QMainWindow, QPushButton, QFormLayout, QLayoutItem

from client.gui.gui_errors import MissingParameters, InvalidParameters
from client.gui.steg_params_validator import validate_lsb_params, validate_bpcs_params, validate_ecc_params
from client.gui.ui_wigdet_generator import generate_custom_button, generate_encryption_key_field_widget, \
    generate_lsb_params_widget, generate_bpcs_params_widget, generate_ecc_params_widget
from client.gui.ui_loader import load_ui

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


class AlgorithmProfiles(IntEnum):
    LSB_ENCODE = 1
    BPCS_ENCODE = 2
    GENERIC_DECODE = 3
    LSB_MAX_CAPACITY = 4
    LSB_CHECK_IF_FITS = 5
    BPCS_MAX_CAPACITY = 6
    BPCS_CHECK_IF_FITS = 7
    BIT_PLANE_SLICING = 8
    IMAGE_DIFF = 9


def get_form_field_text(form_widget: QLayoutItem) -> str:
    return form_widget.itemAt(0, QFormLayout.ItemRole.FieldRole).widget().text()


class StegastatterApplication:
    def __init__(self, /):
        super().__init__()
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
        self.main_window.statusBar().showMessage("Hello")

        self.connect_actions()

        self.main_window.show()

    def reset_selected_paths(self):
        self.selected_vessel_input_path = None
        self.selected_stegged_input_path = None
        self.selected_stegged_output_path = None
        self.selected_message_input_path = None
        self.selected_message_output_path = None
        self.selected_token_input_path = None
        self.selected_token_output_path = None

    def connect_actions(self):
        self.main_window.action_encode_lsb.triggered.connect(self.use_lsb_encoding_widget)
        self.main_window.action_encode_bpcs.triggered.connect(self.use_bpcs_encoding_widget)
        self.main_window.action_decode_generic.triggered.connect(self.use_decoding_widget)
        self.main_window.action_capacity_max_calculation_lsb.triggered.connect(self.use_lsb_max_capacity_widget)
        self.main_window.action_capacity_max_calculation_bpcs.triggered.connect(self.use_bpcs_max_capacity_widget)
        self.main_window.action_capacity_can_fit_lsb.triggered.connect(self.use_lsb_check_fits_widget)
        self.main_window.action_capacity_can_fit_bpcs.triggered.connect(self.use_bpcs_check_fits_widget)
        self.main_window.action_slice_image_bit_planes.triggered.connect(self.use_bit_plane_slicing_widget)
        self.main_window.action_get_diff.triggered.connect(self.use_image_diff_widget)

    def prompt_get_vessel_input_path(self):
        self.selected_vessel_input_path = QFileDialog.getOpenFileName(self.main_window,
                                                                      "Select an existing image to use as a "
                                                                      "Vessel Image",
                                                                      filter=IMAGE_FILTER)[0]

    def prompt_get_stegged_input_path(self):
        self.selected_stegged_input_path = QFileDialog.getOpenFileName(self.main_window,
                                                                       "Select an existing image to extract "
                                                                       "data from",
                                                                       filter=IMAGE_FILTER)[0]

    def prompt_get_stegged_output_path(self):
        self.selected_stegged_output_path = QFileDialog.getSaveFileName(self.main_window, "Select where to save the "
                                                                                          "Stegged Image",
                                                                        filter=IMAGE_FILTER)[0]

    def prompt_get_message_input_path(self):
        self.selected_message_input_path = QFileDialog.getOpenFileName(self.main_window,
                                                                       "Select a file to embed into an image",
                                                                       filter=ANY_FILE_FILTER)[0]

    def prompt_get_message_output_path(self):
        self.selected_message_output_path = QFileDialog.getSaveFileName(self.main_window, "Select where to save the "
                                                                                          "extracted data",
                                                                        filter=ANY_FILE_FILTER)[0]

    def prompt_get_token_input_path(self):
        self.selected_token_input_path = QFileDialog.getOpenFileName(self.main_window,
                                                                     "Select the token that contains the "
                                                                     "extracting algorithm parameters for this image",
                                                                     filter=BIN_FILE_FILTER)[0]

    def prompt_get_token_output_path(self):
        self.selected_token_output_path = QFileDialog.getSaveFileName(self.main_window,
                                                                      "Select where to save the token "
                                                                      "that contains all the algorithm parameters",
                                                                      filter=BIN_FILE_FILTER)[0]

    def prompt_get_image_diff_input_1_path(self):
        self.selected_image_diff_input_1 = QFileDialog.getOpenFileName(self.main_window,
                                                                       "Select the first image to compare",
                                                                       filter=IMAGE_FILTER)[0]

    def prompt_get_image_diff_input_2_path(self):
        self.selected_image_diff_input_2 = QFileDialog.getOpenFileName(self.main_window,
                                                                       "Select the second image to compare",
                                                                       filter=IMAGE_FILTER)[0]

    def prompt_get_image_diff_output_path(self):
        self.selected_image_diff_output_path = QFileDialog.getSaveFileName(self.main_window,
                                                                           "Select where to save the image that "
                                                                           "contains the diffrence between the "
                                                                           "provided images",
                                                                           filter=IMAGE_FILTER)[0]

    def prompt_get_bit_plane_slicing_output_folder_path(self):
        self.selected_bit_plane_slicing_output_folder_path = QFileDialog.getExistingDirectory(self.main_window,
                                                                                              "Select where to save "
                                                                                              "the sliced bit planes "
                                                                                              "of the provided "
                                                                                              "image")

    def create_linked_encoding_widget(self) -> QWidget:
        """
        For encode we need:
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
            case AlgorithmProfiles.LSB_ENCODE:
                layout.addWidget(generate_lsb_params_widget())
            case AlgorithmProfiles.BPCS_ENCODE:
                layout.addWidget(generate_bpcs_params_widget())

        layout.addWidget(generate_ecc_params_widget())

        return widget

    def create_linked_decoding_widget(self) -> QWidget:
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
            case AlgorithmProfiles.LSB_MAX_CAPACITY | AlgorithmProfiles.LSB_CHECK_IF_FITS:
                layout.addWidget(generate_lsb_params_widget())
            case AlgorithmProfiles.BPCS_MAX_CAPACITY | AlgorithmProfiles.BPCS_CHECK_IF_FITS:
                layout.addWidget(generate_bpcs_params_widget())

        layout.addWidget(generate_ecc_params_widget())

        return widget

    def create_linked_check_fits_widget(self) -> QWidget:
        widget = self.create_linked_max_capacity_widget()

        widget.layout().addWidget(generate_custom_button(MESSAGE_INPUT_FILE_LABEL, self.prompt_get_message_input_path))

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

        return widget

    def create_linked_start_button(self) -> QPushButton:
        dialog_button = QPushButton("Start")
        dialog_button.setCheckable(True)
        dialog_button.toggled.connect(self.direct_to_matching_action)

        return dialog_button

    def use_lsb_encoding_widget(self):
        self.selected_algorithm_profile = AlgorithmProfiles.LSB_ENCODE
        widget = self.create_linked_encoding_widget()
        self.update_menu_widget(widget)

    def use_bpcs_encoding_widget(self):
        self.selected_algorithm_profile = AlgorithmProfiles.BPCS_ENCODE
        widget = self.create_linked_encoding_widget()
        self.update_menu_widget(widget)

    def use_decoding_widget(self):
        self.selected_algorithm_profile = AlgorithmProfiles.GENERIC_DECODE
        widget = self.create_linked_decoding_widget()
        self.update_menu_widget(widget)

    def use_lsb_max_capacity_widget(self):
        self.selected_algorithm_profile = AlgorithmProfiles.LSB_MAX_CAPACITY
        widget = self.create_linked_max_capacity_widget()
        self.update_menu_widget(widget)

    def use_bpcs_max_capacity_widget(self):
        self.selected_algorithm_profile = AlgorithmProfiles.BPCS_MAX_CAPACITY
        widget = self.create_linked_max_capacity_widget()
        self.update_menu_widget(widget)

    def use_lsb_check_fits_widget(self):
        self.selected_algorithm_profile = AlgorithmProfiles.LSB_CHECK_IF_FITS
        widget = self.create_linked_check_fits_widget()
        self.update_menu_widget(widget)

    def use_bpcs_check_fits_widget(self):
        self.selected_algorithm_profile = AlgorithmProfiles.BPCS_CHECK_IF_FITS
        widget = self.create_linked_check_fits_widget()
        self.update_menu_widget(widget)

    def use_bit_plane_slicing_widget(self):
        self.selected_algorithm_profile = AlgorithmProfiles.BIT_PLANE_SLICING
        widget = self.create_linked_bit_plane_slicing_widget()
        self.update_menu_widget(widget)

    def use_image_diff_widget(self):
        self.selected_algorithm_profile = AlgorithmProfiles.IMAGE_DIFF
        widget = self.create_linked_image_diff_widget()
        self.update_menu_widget(widget)

    def update_menu_widget(self, widget: QWidget):
        self.reset_selected_paths()
        widget.layout().addStretch()

        widget.layout().addWidget(self.create_linked_start_button())

        self.main_window.setMinimumSize(widget.minimumSize())
        self.main_window.setCentralWidget(widget)

    def direct_to_matching_action(self, checked: bool):
        if checked:
            self.initiate_steganography_action()
        else:
            pass  # TODO: Connect to matching function

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

    def get_encoding_params(self) -> tuple[str, str, str]:
        encryption_key = self.get_encryption_key_at(4)
        block_size, symbol_num = self.get_ecc_params_at(6)
        return encryption_key, block_size, symbol_num

    def initiate_steganography_action(self):
        try:
            match self.selected_algorithm_profile:
                case AlgorithmProfiles.LSB_ENCODE:
                    self.start_lsb_encode()
                case AlgorithmProfiles.BPCS_ENCODE:
                    self.start_bpcs_encode()
                case AlgorithmProfiles.GENERIC_DECODE:
                    self.validate_decode_paths()
                case AlgorithmProfiles.LSB_MAX_CAPACITY:
                    self.start_lsb_max_capacity()
                case AlgorithmProfiles.LSB_CHECK_IF_FITS:
                    self.start_lsb_check_if_fits()
                case AlgorithmProfiles.BPCS_MAX_CAPACITY:
                    self.start_bpcs_max_capacity()
                case AlgorithmProfiles.BPCS_CHECK_IF_FITS:
                    self.start_bpcs_check_if_fits()
                case AlgorithmProfiles.BIT_PLANE_SLICING:
                    self.start_bit_plane_slicing()
                case AlgorithmProfiles.IMAGE_DIFF:
                    self.start_image_diff()

        except (InvalidParameters, MissingParameters) as e:
            self.main_window.statusBar().showMessage(str(e))

    def validate_encode_paths(self):
        if self.selected_vessel_input_path is None:
            raise MissingParameters("A vessel image input path is required.")
        if self.selected_stegged_output_path is None:
            raise MissingParameters("A stegged image output path is required.")
        if self.selected_message_input_path is None:
            raise MissingParameters("A message file input path is required.")
        if self.selected_token_output_path is None:
            raise MissingParameters("A token file output path is required.")

    def validate_decode_paths(self):
        if self.selected_stegged_input_path is None:
            raise MissingParameters("A stegged image input path is required.")
        if self.selected_message_output_path is None:
            raise MissingParameters("A message file output path is required.")
        if self.selected_token_input_path is None:
            raise MissingParameters("A token file input path is required.")

    def validate_max_capacity_paths(self):
        if self.selected_vessel_input_path is None:
            raise MissingParameters("A vessel image input path is required.")

    def validate_check_fits_paths(self):
        self.validate_max_capacity_paths()
        if self.selected_message_input_path is None:
            raise MissingParameters("A message file input path is required.")

    def validate_bit_plane_slicing_paths(self):
        if self.selected_vessel_input_path is None:
            raise MissingParameters("An image input path is required.")
        if self.selected_bit_plane_slicing_output_folder_path is not None:
            raise MissingParameters("A sliced bit planes output folder path is required.")

    def validate_image_diff_paths(self):
        if self.selected_image_diff_input_1 is None:
            raise MissingParameters("A 1st image input path for image diff is required.")
        if self.selected_image_diff_input_2 is None:
            raise MissingParameters("A 2nd image input path for image diff is required.")
        if self.selected_image_diff_output_path is None:
            raise MissingParameters("An image diff output path is required.")

    def start_lsb_encode(self):
        self.validate_encode_paths()
        encryption_key, block_size, symbol_num = self.get_encoding_params()
        num_of_sacrificed_bits = self.get_form_field_text_at_group_box_at(5, 0)
        validate_lsb_params(num_of_sacrificed_bits)
        validate_ecc_params(block_size, symbol_num)

        block_size = int(block_size)
        symbol_num = int(symbol_num)
        num_of_sacrificed_bits = int(num_of_sacrificed_bits)

    def start_bpcs_encode(self):
        self.validate_encode_paths()
        encryption_key, block_size, symbol_num = self.get_encoding_params()
        min_alpha = self.get_form_field_text_at_group_box_at(5, 0)
        validate_bpcs_params(min_alpha)
        validate_ecc_params(block_size, symbol_num)

        block_size = int(block_size)
        symbol_num = int(symbol_num)
        min_alpha = float(min_alpha)

    def start_lsb_max_capacity(self):
        self.validate_max_capacity_paths()
        block_size, symbol_num = self.get_ecc_params_at(2)
        num_of_sacrificed_bits = self.get_form_field_text_at_group_box_at(1, 0)
        validate_lsb_params(num_of_sacrificed_bits)
        validate_ecc_params(block_size, symbol_num)

        block_size = int(block_size)
        symbol_num = int(symbol_num)
        num_of_sacrificed_bits = int(num_of_sacrificed_bits)

    def start_bpcs_max_capacity(self):
        self.validate_max_capacity_paths()
        block_size, symbol_num = self.get_ecc_params_at(2)
        min_alpha = self.get_form_field_text_at_group_box_at(1, 0)
        validate_bpcs_params(min_alpha)
        validate_ecc_params(block_size, symbol_num)

        block_size = int(block_size)
        symbol_num = int(symbol_num)
        min_alpha = float(min_alpha)

    def start_lsb_check_if_fits(self):
        # TODO: Modify after lsb max capacity is finished
        self.validate_check_fits_paths()
        block_size, symbol_num = self.get_ecc_params_at(2)
        num_of_sacrificed_bits = self.get_form_field_text_at_group_box_at(1, 0)
        validate_lsb_params(num_of_sacrificed_bits)
        validate_ecc_params(block_size, symbol_num)

    def start_bpcs_check_if_fits(self):
        # TODO: Modify after bpcs max capacity is finished
        self.validate_check_fits_paths()
        block_size, symbol_num = self.get_ecc_params_at(2)
        min_alpha = self.get_form_field_text_at_group_box_at(1, 0)
        validate_bpcs_params(min_alpha)
        validate_ecc_params(block_size, symbol_num)

    def start_bit_plane_slicing(self):
        self.validate_bit_plane_slicing_paths()

    def start_image_diff(self):
        self.validate_image_diff_paths()
