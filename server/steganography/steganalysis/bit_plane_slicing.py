import io
import multiprocessing
import numpy as np
from PIL import Image

from server.steganography.image_utils import open_image_from_bytes


def slice_rgb_bit_planes(image_bytes: bytes):
    update_logger = multiprocessing.get_logger()

    image = open_image_from_bytes(image_bytes)

    update_logger.info("Slicing image into separate bitplanes...")
    for channel in image.getbands():
        c_image = np.array(image.getchannel(channel))
        update_logger.info(f"Channel: {channel}")

        for bit_index in range(0, 8):
            update_logger.info(f"Bit index: {bit_index}")
            slice_name = f"Bitplane {channel}{str(7 - bit_index)}.png"
            bitplane_slice = Image.new("1", image.size)
            chk_val = int(f"0b{bit_index * "0"}1{((7 - bit_index) * "0")}", 2)

            for y in range(c_image.shape[0]):
                for x in range(c_image.shape[1]):
                    src_val = c_image[y][x]
                    if chk_val & src_val > 0:
                        match channel:
                            case "R":
                                bitplane_slice.putpixel((x, y), 1)
                            case "G":
                                bitplane_slice.putpixel((x, y), 1)
                            case "B":
                                bitplane_slice.putpixel((x, y), 1)

            image_bytes = io.BytesIO()
            bitplane_slice.save(image_bytes, format="PNG")
            yield slice_name, image_bytes.getvalue()
