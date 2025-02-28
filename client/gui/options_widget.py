import sys
import types

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QComboBox, QGroupBox, QVBoxLayout, QCheckBox, QPushButton, QHBoxLayout

from client.gui.algorithm_options import OPTIONS
from client.gui.bpcs_widgets import BPCSEncodeMenuWidget


class AlgorithmSelectorWidget(QGroupBox):
    def __init__(self):
        super().__init__()
        self.vbox = QVBoxLayout()

        self.algorithm_selector_widget = QComboBox()
        self.action_selector_widget = QComboBox()
        self.algorithm_menu_widget = QGroupBox()

        for option in OPTIONS.keys():
            self.algorithm_selector_widget.addItem(option)
        self.algorithm_selector_widget.activated.connect(self.update_action_selector_widget)

        self.update_action_selector_widget()
        self.action_selector_widget.activated.connect(self.update_menu_widget)

        self.vbox.addWidget(self.algorithm_selector_widget)
        self.vbox.addWidget(self.action_selector_widget)
        self.vbox.addWidget(self.algorithm_menu_widget)

        self.vbox.addStretch()
        self.setLayout(self.vbox)

    def update_action_selector_widget(self):
        self.action_selector_widget.clear()
        option = self.algorithm_selector_widget.currentText()
        for action in OPTIONS[option].keys():
            self.action_selector_widget.addItem(action)
        self.update_menu_widget()

    def update_menu_widget(self):
        option = self.algorithm_selector_widget.currentText(), self.action_selector_widget.currentText()
        new_widget = OPTIONS[option[0]][option[1]]()
        self.algorithm_menu_widget.setLayout(new_widget.layout())

