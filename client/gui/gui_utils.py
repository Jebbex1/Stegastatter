from PySide6.QtWidgets import QLayout, QLayoutItem, QFormLayout


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


def get_form_field_text(form_widget: QLayoutItem) -> str:
    return form_widget.itemAt(0, QFormLayout.ItemRole.FieldRole).widget().text()
