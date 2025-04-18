from typing import Callable

from PySide6.QtWidgets import QPushButton

from client.gui.ui_loader import load_ui


def generate_custom_button(button_title: str, button_trigger: Callable):
    button = QPushButton(button_title)
    button.clicked.connect(button_trigger)
    return button


def generate_encryption_key_field_widget():
    return load_ui("client/gui/ui_files/encryption_key_field.ui")


def generate_lsb_params_widget():
    return load_ui("client/gui/ui_files/lsb_parameters.ui")


def generate_bpcs_params_widget():
    return load_ui("client/gui/ui_files/bpcs_parameters.ui")


def generate_ecc_params_widget():
    return load_ui("client/gui/ui_files/ecc_parameters.ui")
