import sys

from PySide6.QtCore import QObject, QEvent
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QApplication, QWidget
from client.gui.application_window import StegastatterApplication


class CloseEventFilterer(QObject):
    def __init__(self, exit_function: callable, /):
        super().__init__()
        self.exit_function = exit_function
        self.closed = False

    def eventFilter(self, widget: QWidget, event: QEvent) -> bool:
        if event.__class__ == QCloseEvent and not self.closed:
            self.closed = True
            self.exit_function()
        return False


if __name__ == '__main__':
    app = QApplication(sys.argv)
    stegastatter = StegastatterApplication()
    app.aboutToQuit.connect(stegastatter.safe_close)
    sys.exit(app.exec())
