import sys

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QDockWidget, QWidget


class MainWindow(QMainWindow):
    def __init__(self, title: str, init_size: QSize, max_size: QSize):
        super().__init__()
        self.setWindowTitle(title)
        self.setMinimumSize(init_size)
        self.setMaximumSize(max_size)
        self.setDockNestingEnabled(True)

    def add_widget_as_dock(self, widget: QWidget, widget_title: str, side: Qt.DockWidgetArea):
        dock_widget = QDockWidget(widget_title, self)
        dock_widget.setWidget(widget)
        self.addDockWidget(side, dock_widget)
        return dock_widget