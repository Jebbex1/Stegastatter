import sys

from PySide6.QtWidgets import QLineEdit, QApplication, QWidget

from client.gui.core_menu_widget import EncodeMenuWidget, DecodeMenuWidget


class BPCSEncodeMenuWidget(EncodeMenuWidget):
    def __init__(self):
        super().__init__()
        self.min_alpha_line_edit = QLineEdit()
        self.min_alpha_line_edit.setPlaceholderText("BPCS Complexity Coefficient")
        self.min_alpha_line_edit.hide()
        self.vbox.addWidget(self.min_alpha_line_edit)

        self.select_input_image_file_button = self.get_image_select_button("Select Input Image",
                                                                           "input_image")
        self.vbox.insertWidget(0, self.select_input_image_file_button)

        self.select_input_message_file_button = self.get_any_file_select_button("Select File to Encode into Image",
                                                                                "input_message")
        self.vbox.insertWidget(1, self.select_input_message_file_button)

    def show_advanced_settings(self):
        super().show_advanced_settings()
        self.min_alpha_line_edit.show()

    def hide_advanced_settings(self):
        super().hide_advanced_settings()
        self.min_alpha_line_edit.hide()


class BPCSDecodeMenunWidget(DecodeMenuWidget):
    def __init__(self):
        super().__init__()
