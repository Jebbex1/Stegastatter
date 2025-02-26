import sys

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QComboBox, QGroupBox, QVBoxLayout, QCheckBox, QPushButton

from client.gui.steg_options import OPTIONS


class SteganographyAlgorithmWidget(QGroupBox):
    def __init__(self):
        super().__init__()

        self.algorithm_widget = QComboBox()
        for option in OPTIONS.keys():
            self.algorithm_widget.addItem(option)

        self.action_widget = QComboBox()
        self.update_action_selector_widget()

        self.vbox = QVBoxLayout()
        self.vbox.addWidget(self.algorithm_widget)
        self.vbox.addWidget(self.action_widget)
        self.vbox.addStretch()

        self.algorithm_widget.currentIndexChanged.connect(self.update_action_selector_widget)
        self.setLayout(self.vbox)

    def update_action_selector_widget(self):
        self.action_widget.clear()
        option = self.algorithm_widget.currentText()
        for action in OPTIONS[option]:
            self.action_widget.addItem(action)
