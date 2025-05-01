from PySide6.QtWidgets import QLayout


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
    layout.deleteLater()
