import sys
import functools

from PySide6.QtWidgets import QWidget, QGroupBox, QCheckBox, QVBoxLayout, QLineEdit, QApplication, QFileDialog, \
    QPushButton

from client.gui.core_action_widget import CoreActionWidget


class EncodeActionWidget(CoreActionWidget):
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
        self.vbox.update()


class BPCSEncodeActionWidget(EncodeActionWidget):
    def __init__(self):
        super().__init__()
        self.min_alpha_line_edit = QLineEdit()
        self.min_alpha_line_edit.setPlaceholderText("BPCS Complexity Coefficient")
        self.min_alpha_line_edit.hide()
        self.vbox.addWidget(self.min_alpha_line_edit)

        self.select_input_image_file_button = self.get_image_select_button("Select Input Image",
                                                                           "input_image")
        self.vbox.insertWidget(2, self.select_input_image_file_button)

        self.select_input_message_file_button = self.get_any_file_select_button("Select File to Encode into Image",
                                                                                "input_message")
        self.vbox.insertWidget(3, self.select_input_message_file_button)

    def show_advanced_settings(self):
        super().show_advanced_settings()
        self.min_alpha_line_edit.show()

    def hide_advanced_settings(self):
        super().hide_advanced_settings()
        self.min_alpha_line_edit.hide()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BPCSEncodeActionWidget()
    window.show()
    sys.exit(app.exec())
