from PySide6.QtWidgets import QCheckBox

from client.gui.menus.core_menus import CoreMenuLayout


class ImageDiffMenuLayout(CoreMenuLayout):
    def __init__(self):
        super().__init__()

        self.select_input_image1_file_button = self.get_any_file_select_button("Select First Image Input File",
                                                                               "input_image1")
        self.addWidget(self.select_input_image1_file_button)

        self.select_input_image2_file_button = self.get_any_file_select_button("Select Second Image Input File",
                                                                               "input_image2")
        self.addWidget(self.select_input_image2_file_button)

        self.calc_exact_diff_checkbox = QCheckBox()
        self.calc_exact_diff_checkbox.setText("Calculate Exact Difference")
        self.calc_exact_diff_checkbox.setChecked(True)
        self.addWidget(self.calc_exact_diff_checkbox)


class BitPlaneSlicingMenuLayout(CoreMenuLayout):
    def __init__(self):
        super().__init__()
        self.select_input_image_file_button = self.get_any_file_select_button("Select Image Input File",
                                                                              "input_image")
        self.addWidget(self.select_input_image_file_button)
