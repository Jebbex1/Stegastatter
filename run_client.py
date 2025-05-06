import sys

from PySide6.QtWidgets import QApplication
from client.gui.application_window import StegastatterApplication


if __name__ == '__main__':
    app = QApplication(sys.argv)
    StegastatterApplication()
    sys.exit(app.exec())
