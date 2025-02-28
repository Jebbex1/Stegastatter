from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QMainWindow, QDockWidget

from client.gui.steg_control_panel_widget import ControlPanelWidget
from client.gui.log_widget import LogWidget


class MainWindow(QMainWindow):
    def __init__(self, title: str, init_size: QSize = QSize(1280, 720)):
        super().__init__()
        self.setWindowTitle(title)
        self.setMinimumSize(init_size)
        self.setDockNestingEnabled(True)

        self.control_panel_widget = ControlPanelWidget()
        cpanel_dock = QDockWidget("Steganography Control Panel")
        cpanel_dock.setWidget(self.control_panel_widget)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, cpanel_dock)

        self.log_widget = LogWidget()
        log_dock = QDockWidget("Request Status")
        log_dock.setWidget(self.log_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, log_dock)



