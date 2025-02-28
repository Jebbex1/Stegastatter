from PySide6.QtWidgets import QGroupBox

from client.gui.bpcs_widgets import BPCSEncodeMenuWidget, BPCSDecodeMenuWidget

OPTIONS = {
    "LSB (Least Significant Bit)": {
        "Encode": QGroupBox,
        "Decode": QGroupBox,
    },
    "BPCS (Bit-Plane Complexity Segmentation)": {
        "Encode": BPCSEncodeMenuWidget,
        "Decode": BPCSDecodeMenuWidget,
        "Check capacity": QGroupBox,
    },
    "Steganalysis": {
        "Get image diffrence": QGroupBox,
        "Slice bit-planes": QGroupBox,
    },
}
