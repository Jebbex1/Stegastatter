from PySide6.QtWidgets import QFileDialog, QGroupBox, QVBoxLayout, QPushButton

OPTIONS = {
    "LSB (Least Significant Bit)": [
        "Encode",
        "Decode"
    ],
    "BPCS (Bit-Plane Complexity Segmentation)": [
        "Encode",
        "Decode",
        "Check capacity"
    ],
    "Steganalysis": [
        "Get image diffrence",
        "Slice bit-planes"
    ],
}


def get_input_image():
    input_image_file_dialog = QFileDialog.getOpenFileName(None, "Select Input Image", "/", "Image Files (*.png *.bmp)")
    return input_image_file_dialog[0]


def get_bpcs_encode_menu():
    group = QGroupBox()
    vbox = QVBoxLayout()

    select_image_button = QPushButton("Select Input image")
