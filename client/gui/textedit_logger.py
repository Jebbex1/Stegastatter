import logging
import multiprocessing
import sys
import threading
import time
from functools import cached_property

from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QTextEdit, QApplication, QMainWindow, QPushButton

from client.gui.ui_loader import load_ui


class Bridge(QObject):
    log = Signal(str)
    move = Signal(QTextCursor.MoveOperation)
    toggle_button = Signal(bool)


class LoggerOperationsHandler(logging.Handler):
    @cached_property
    def bridge(self):
        return Bridge()

    def __init__(self, status_widget: QTextEdit, start_button: QPushButton):
        super().__init__()
        self.widget = status_widget
        self.start_button = start_button
        self.bridge.log.connect(self.widget.append)
        self.bridge.move.connect(self.widget.moveCursor)
        self.bridge.toggle_button.connect(self.start_button.setChecked)

    def emit(self, record: logging.LogRecord):
        pass
