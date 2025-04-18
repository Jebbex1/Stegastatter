from enum import IntEnum

from PySide6.QtWidgets import QFileDialog, QWidget, QVBoxLayout, QDockWidget, QLabel
from PySide6.QtCore import Qt

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
    LSB_CHECK_CAPACITY = 5
    BPCS_MAX_CAPACITY = 6
    BPCS_CHECK_CAPACITY = 7
    BIT_PLANE_SLICING = 8
    IMAGE_DIFF = 9


def foo():
    print("foo")


class Application:
    def __init__(self, /):
        super().__init__()
        self.selected_vessel_input_path = None
        self.selected_stegged_input_path = None
        self.selected_stegged_output_path = None
        self.selected_message_input_path = None
        self.selected_message_output_path = None
        self.selected_token_input_path = None
        self.selected_token_output_path = None
        self.selected_algorithm_profile = 0

        self.main_window = load_ui("client/gui/ui_files/main_window.ui")
        self.selected_algorithm_widget = None

        self.main_window.action_encode_lsb.triggered.connect(self.dock_linked_encoding_widget)
        self.main_window.action_encode_bpcs.triggered.connect(self.dock_linked_encoding_widget)
        self.main_window.action_decode_generic.triggered.connect(self.create_linked_decoding_widget)
        self.main_window.action_capacity_max_calculation_lsb.triggered.connect(self.create_linked_max_capacity_widget)
        self.main_window.action_capacity_max_calculation_bpcs.triggered.connect(self.create_linked_max_capacity_widget)
        self.main_window.action_capacity_can_fit_lsb.triggered.connect(self.create_linked_check_fits_widget)
        self.main_window.action_capacity_can_fit_bpcs.triggered.connect(self.create_linked_check_fits_widget)
        self.main_window.action_slice_image_bit_planes.triggered.connect(self.create_linked_bit_plane_slicing_widget)
        self.main_window.action_get_diff.triggered.connect(self.create_linked_image_diff_widget)

        self.main_window.show()

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

    def dock_linked_encoding_widget(self):
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
        self.add_widget_as_algorithm_profile_dock(widget)

        return widget

    def create_linked_decoding_widget(self):
        widget = QWidget()
        widget.setLayout(QVBoxLayout())
        layout = widget.layout()

        layout.addWidget(generate_custom_button(STEGGED_IMAGE_INPUT_LABEL, self.prompt_get_stegged_input_path))
        layout.addWidget(generate_custom_button(MESSAGE_OUTPUT_FILE_LABEL, self.prompt_get_message_output_path))
        layout.addWidget(generate_custom_button(TOKEN_INPUT_FILE_LABEL, self.prompt_get_token_input_path))
        self.add_widget_as_algorithm_profile_dock(widget)

        return widget

    def create_linked_max_capacity_widget(self):
        widget = QWidget()
        widget.setLayout(QVBoxLayout())
        layout = widget.layout()

        layout.addWidget(generate_custom_button(VESSEL_IMAGE_INPUT_LABEL, self.prompt_get_vessel_input_path))

        match self.selected_algorithm_profile:
            case AlgorithmProfiles.LSB_ENCODE:
                layout.addWidget(generate_lsb_params_widget())
            case AlgorithmProfiles.BPCS_ENCODE:
                layout.addWidget(generate_bpcs_params_widget())

        layout.addWidget(generate_ecc_params_widget())
        self.add_widget_as_algorithm_profile_dock(widget)

        return widget

    def create_linked_check_fits_widget(self):
        widget = self.create_linked_max_capacity_widget()

        widget.layout().addWidget(generate_custom_button(VESSEL_IMAGE_INPUT_LABEL, self.prompt_get_vessel_input_path))
        self.add_widget_as_algorithm_profile_dock(widget)

        return widget

    def create_linked_bit_plane_slicing_widget(self):
        widget = QWidget()
        widget.setLayout(QVBoxLayout())
        layout = widget.layout()

        layout.addWidget(generate_custom_button("Select Image Input File", self.prompt_get_vessel_input_path))
        self.add_widget_as_algorithm_profile_dock(widget)

        return widget

    def create_linked_image_diff_widget(self):
        widget = QWidget()
        widget.setLayout(QVBoxLayout())
        layout = widget.layout()

        layout.addWidget(generate_custom_button("Select 1st Image Input File", self.prompt_get_vessel_input_path))
        layout.addWidget(generate_custom_button("Select 2nd Image Input File", self.prompt_get_vessel_input_path))
        self.add_widget_as_algorithm_profile_dock(widget)

        return widget

    def add_widget_as_algorithm_profile_dock(self, widget: QWidget):
        dock = QDockWidget()
        dock.setWindowTitle("Current Algorithm Profile")

        widget.layout().addStretch()

        dock.setWidget(widget)

        self.main_window.removeDockWidget(self.selected_algorithm_widget)
        self.main_window.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)
        self.selected_algorithm_widget = dock
