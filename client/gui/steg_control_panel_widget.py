from PySide6.QtWidgets import QComboBox, QGroupBox, QVBoxLayout, QLayout

from client.gui.menu_options import OPTIONS
from client.gui.menus.core_menus import CoreMenuLayout


def clear_layout(layout: QLayout):
    if layout is None:
        return
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.setParent(None)
            widget.deleteLater()
        else:
            clear_layout(item.layout())


def copy_layout_contents(source_layout: QLayout, target_layout: QLayout):
    clear_layout(target_layout)

    while source_layout.count():
        item = source_layout.takeAt(0)
        if item.widget():
            target_layout.addWidget(item.widget())


class ControlPanelWidget(QGroupBox):
    def __init__(self):
        super().__init__()
        self.vbox = QVBoxLayout()

        self.algorithm_selector_widget = QComboBox()
        self.action_selector_widget = QComboBox()
        self.algorithm_menu_container_widget = QGroupBox()
        self.algorithm_menu_container_widget.setTitle("Algorithm Parameters")
        self.algorithm_menu_container_widget.setLayout(CoreMenuLayout())

        for option in OPTIONS.keys():
            self.algorithm_selector_widget.addItem(option)
        self.algorithm_selector_widget.activated.connect(self.update_action_selector_widget)

        self.update_action_selector_widget()
        self.action_selector_widget.activated.connect(self.update_menu_widget)

        self.vbox.addWidget(self.algorithm_selector_widget)
        self.vbox.addWidget(self.action_selector_widget)
        self.vbox.addWidget(self.algorithm_menu_container_widget)

        self.vbox.addStretch()
        self.setLayout(self.vbox)
        self.setObjectName("ColoredGroupBox")
        self.setStyleSheet("ControlPanelWidget#ColoredGroupBox {border: 0px;}")

    def update_action_selector_widget(self):
        self.action_selector_widget.clear()
        option = self.algorithm_selector_widget.currentText()
        for action in OPTIONS[option].keys():
            self.action_selector_widget.addItem(action)
        self.update_menu_widget()

    def update_menu_widget(self):
        option = self.algorithm_selector_widget.currentText(), self.action_selector_widget.currentText()
        new_layout = OPTIONS[option[0]][option[1]]()
        copy_layout_contents(new_layout, self.algorithm_menu_container_widget.layout())
