import sys

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QComboBox, QGroupBox, QVBoxLayout, QCheckBox, QPushButton

from client.gui.algorithm_options import OPTIONS


class AlgorithmSelectorWidget(QGroupBox):
    def __init__(self):
        super().__init__()

        self.algorithm_selector_widget = QComboBox()
        for option in OPTIONS.keys():
            self.algorithm_selector_widget.addItem(option)
        self.algorithm_selector_widget.currentIndexChanged.connect(self.update_action_selector_widget)

        self.action_selector_widget = QComboBox()
        self.update_action_selector_widget()

        self.vbox = QVBoxLayout()
        self.vbox.addWidget(self.algorithm_selector_widget)
        self.vbox.addWidget(self.action_selector_widget)
        self.vbox.addStretch()

        self.setLayout(self.vbox)

    def update_action_selector_widget(self):
        self.action_selector_widget.clear()
        option = self.algorithm_selector_widget.currentText()
        for action in OPTIONS[option]:
            self.action_selector_widget.addItem(action)
