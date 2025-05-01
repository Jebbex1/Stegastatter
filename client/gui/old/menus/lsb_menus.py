from client.gui.old.menus.core_menus import EncodeMenuLayout, DecodeMenuLayout


class LSBEncodeMenuLayout(EncodeMenuLayout):
    def __init__(self):
        super().__init__()
        self.select_input_image_file_button = self.get_image_select_button("Select Input Image",
                                                                           "input_image")
        self.insertWidget(0, self.select_input_image_file_button)


class LSBDecodeMenuLayout(DecodeMenuLayout):
    def __init__(self):
        super().__init__()


class LSBCapacityMenuLayout(LSBEncodeMenuLayout):
    def __init__(self):
        super().__init__()
        self.removeWidget(self.key_line_edit)
