import functools
import sys

from PySide6.QtWidgets import QWidget, QGroupBox, QVBoxLayout, QFileDialog, QLayout, QPushButton, QCheckBox, QLineEdit, \
    QApplication
from PySide6.QtCore import Qt


class CoreMenuWidget(QGroupBox):
    def __init__(self):
        super().__init__()
        self.vbox = QVBoxLayout()
        self.vbox.addStretch()
        self.setLayout(self.vbox)

        self.selected_files = {}

    def select_existing_file(self, caption: str, file_identifier: str, file_filter: str):
        self.selected_files[file_identifier] = QFileDialog.getOpenFileName(self,
                                                                           caption=caption,
                                                                           filter=file_filter)[0]

    def get_image_select_button(self, button_title: str, file_identifier: str):
        select_image_button = QPushButton(button_title)
        select_image_button.pressed.connect(functools.partial(self.select_existing_file,
                                                              "Select Image",
                                                              file_identifier,
                                                              "Lossless Image Files (*.png *.bmp)"))
        return select_image_button

    def get_any_file_select_button(self, button_title: str, file_identifier: str):
        select_file_button = QPushButton(button_title)
        select_file_button.pressed.connect(functools.partial(self.select_existing_file,
                                                             "Select File",
                                                             file_identifier,
                                                             "All Files (*.*)"))
        return select_file_button

    def get_bin_file_select_button(self, button_title: str, file_identifier: str):
        select_file_button = QPushButton(button_title)
        select_file_button.pressed.connect(functools.partial(self.select_existing_file,
                                                             "Select .bin File",
                                                             file_identifier,
                                                             "Binary Files (*.bin)"))
        return select_file_button


class EncodeMenuWidget(CoreMenuWidget):
    def __init__(self):
        super().__init__()

        self.show_advanced_settings_checkbox = QCheckBox()
        self.show_advanced_settings_checkbox.setText("Show advanced settings")
        self.show_advanced_settings_checkbox.setChecked(False)
        self.show_advanced_settings_checkbox.stateChanged.connect(self.update_advanced_settings_state)

        self.key_line_edit = QLineEdit()
        self.key_line_edit.setPlaceholderText("Encryption Key")

        self.ecc_block_size_line_edit = QLineEdit()
        self.ecc_block_size_line_edit.setPlaceholderText("RS-ECC Block Size")
        self.ecc_block_size_line_edit.hide()

        self.ecc_symbol_num_line_edit = QLineEdit()
        self.ecc_symbol_num_line_edit.setPlaceholderText("RS-ECC Symbol Number")
        self.ecc_symbol_num_line_edit.hide()

        self.vbox.addWidget(self.key_line_edit)
        self.vbox.addWidget(self.show_advanced_settings_checkbox)
        self.vbox.addWidget(self.ecc_block_size_line_edit)
        self.vbox.addWidget(self.ecc_symbol_num_line_edit)

    def show_advanced_settings(self):
        self.ecc_block_size_line_edit.show()
        self.ecc_symbol_num_line_edit.show()

    def hide_advanced_settings(self):
        self.ecc_block_size_line_edit.hide()
        self.ecc_symbol_num_line_edit.hide()

    def update_advanced_settings_state(self):
        if self.show_advanced_settings_checkbox.isChecked():
            self.show_advanced_settings()
        else:
            self.hide_advanced_settings()


class DecodeMenuWidget(CoreMenuWidget):
    def __init__(self):
        super().__init__()
        self.select_input_image_file_button = self.get_image_select_button("Select Input Image",
                                                                           "input_image")
        self.vbox.insertWidget(0, self.select_input_image_file_button)

        self.select_input_token_file_button = self.get_bin_file_select_button("Select Decoding Token",
                                                                              "input_token")
        self.vbox.insertWidget(1, self.select_input_token_file_button)
