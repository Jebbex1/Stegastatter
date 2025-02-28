from typing import Type

from client.gui.menus.bpcs_menus import BPCSEncodeMenuLayout, BPCSDecodeMenuLayout, BPCSCapacityMenuLayout
from client.gui.menus.core_menus import CoreMenuLayout
from client.gui.menus.lsb_menus import LSBCapacityMenuLayout, LSBDecodeMenuLayout, LSBEncodeMenuLayout
from client.gui.menus.steganalysis_menus import ImageDiffMenuLayout, BitPlaneSlicingMenuLayout

OPTIONS: dict[str, dict[str, Type[CoreMenuLayout]]] = {
    "LSB (Least Significant Bit)": {
        "Encode": LSBEncodeMenuLayout,
        "Decode": LSBDecodeMenuLayout,
        "Check Capacity": LSBCapacityMenuLayout,
    },
    "BPCS (Bit-Plane Complexity Segmentation)": {
        "Encode": BPCSEncodeMenuLayout,
        "Decode": BPCSDecodeMenuLayout,
        "Check Capacity": BPCSCapacityMenuLayout,
    },
    "Steganalysis": {
        "Get Image Diffrence": ImageDiffMenuLayout,
        "Slice Bit-Planes": BitPlaneSlicingMenuLayout,
    },
}
