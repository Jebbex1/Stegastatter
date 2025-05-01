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


class LoggerOperationsHandler(logging.Handler):
    @cached_property
    def bridge(self):
        return Bridge()

    def __init__(self, status_widget: QTextEdit):
        super().__init__()
        self.widget = status_widget
        self.bridge.log.connect(self.widget.append)
        self.bridge.move.connect(self.widget.moveCursor)

    def emit(self, record: logging.LogRecord):
        pass


def t1():
    print(1)
    time.sleep(2)
    print(2)
    l1 = multiprocessing.get_logger()
    l1.info("Hello")
    l1.warning("HAII")
    print(3)


class C:
    def __init__(self):
        self.s = load_ui("ui_files/status_log.ui")


if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = QMainWindow()

    c = C()

    status_logger_handler = LoggerOperationsHandler(c.s)

    # log to text box
    l = multiprocessing.get_logger()
    l.addHandler(status_logger_handler)
    l.setLevel(logging.INFO)

    window.setCentralWidget(c.s)
    window.show()

    threading.Thread(target=t1).start()

    sys.exit(app.exec())
