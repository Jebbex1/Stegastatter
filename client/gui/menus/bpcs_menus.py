from PySide6.QtWidgets import QLineEdit

from client.gui.menus.core_menus import EncodeMenuLayout, DecodeMenuLayout


class BPCSEncodeMenuLayout(EncodeMenuLayout):
    def __init__(self):
        super().__init__()
        self.min_alpha_line_edit = QLineEdit()
        self.min_alpha_line_edit.setPlaceholderText("BPCS Complexity Coefficient")
        self.min_alpha_line_edit.hide()
        self.addWidget(self.min_alpha_line_edit)

        self.select_input_image_file_button = self.get_image_select_button("Select Input Image",
                                                                           "input_image")
        self.insertWidget(0, self.select_input_image_file_button)

    def show_advanced_settings(self):
        super().show_advanced_settings()
        self.min_alpha_line_edit.show()

    def hide_advanced_settings(self):
        super().hide_advanced_settings()
        self.min_alpha_line_edit.hide()


class BPCSDecodeMenuLayout(DecodeMenuLayout):
    def __init__(self):
        super().__init__()


class BPCSCapacityMenuLayout(BPCSEncodeMenuLayout):
    def __init__(self):
        super().__init__()
        self.removeWidget(self.key_line_edit)
