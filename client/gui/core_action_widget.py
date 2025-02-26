import functools

from PySide6.QtWidgets import QWidget, QGroupBox, QVBoxLayout, QFileDialog, QLayout, QPushButton
from PySide6.QtCore import Qt


class CoreActionWidget(QGroupBox):
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
