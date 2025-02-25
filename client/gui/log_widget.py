import logging
import multiprocessing

from PySide6.QtWidgets import QTextEdit
from PySide6.QtGui import QFont


class LogWidget(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setFont(QFont("Arial", 10))
        text_logger = multiprocessing.get_logger()
        text_logger.setLevel(logging.INFO)
        text_logger.addFilter(self.add_text)

    def add_text(self, record: logging.LogRecord) -> bool:
        self.append(record.getMessage())
        return True
