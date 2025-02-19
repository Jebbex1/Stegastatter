import sys
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QDockWidget, QWidget


# Subclass QMainWindow to customize your application's main window
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


app = QApplication(sys.argv)

window = MainWindow("Testing", QSize(640, 360), QSize(1280, 720))

left_button = QPushButton("This is a left button")
l_button_dock = window.add_widget_as_dock(left_button, "Left Button", Qt.DockWidgetArea.LeftDockWidgetArea)
l_button_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
l_button_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetFloatable)

right_button = QPushButton("This is a right button")
r_button_dock = window.add_widget_as_dock(right_button, "Right Button", Qt.DockWidgetArea.LeftDockWidgetArea)
r_button_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)

bottom_button = QPushButton("This is a bottom button")
b_button_dock = window.add_widget_as_dock(bottom_button, "Bottom Button", Qt.DockWidgetArea.BottomDockWidgetArea)
b_button_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)

window.setCentralWidget(QPushButton("Hello there"))

window.show()

app.exec()
