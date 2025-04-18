from PySide6.QtCore import QFile
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QWidget


def load_ui(ui_file_path: str) -> QWidget:
    ui_file = QFile(ui_file_path)
    loader = QUiLoader()

    widget = loader.load(ui_file)
    ui_file.close()

    return widget

