import numpy as np
from PIL import Image
import os


def slice_rgb_bit_planes(input_image_path: str, out_folder_path: str):
    image = Image.open(input_image_path)
    image = image.convert('RGB')
    os.makedirs(out_folder_path, exist_ok=True)

    for channel in image.getbands():
        c_image = np.array(image.getchannel(channel))
        print(f"Channel: {channel}")
        for bit_index in range(0, 8):
            print(f"Bit index: {bit_index}")
            temp_name = f'Bitplane {channel}{str(7 - bit_index)}.png'
            temp_image = Image.new("RGB", image.size)
            chk_val = int(f"0b{bit_index * "0"}1{((7 - bit_index) * "0")}", 2)
            for y in range(c_image.shape[0]):
                for x in range(c_image.shape[1]):

                    src_val = c_image[y][x]

                    if chk_val & src_val > 0:
                        match channel:
                            case "R":
                                temp_image.putpixel((x, y), (255, 0, 0))
                            case "G":
                                temp_image.putpixel((x, y), (0, 255, 0))
                            case "B":
                                temp_image.putpixel((x, y), (0, 0, 255))

            temp_image.save(f"{out_folder_path}/{temp_name}")


if __name__ == '__main__':
    slice_rgb_bit_planes("out1.png",
                         ".test")
