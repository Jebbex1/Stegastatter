from PIL import Image


def show_diff(image1_path: str, image2_path: str, image_mode, output_path: str, exact_diff: bool = True):
    img1 = Image.open(image1_path)
    img2 = Image.open(image2_path)
    img1 = img1.convert(image_mode)
    img2 = img2.convert(image_mode)

    assert img1.size == img2.size

    diff = Image.new(image_mode, img1.size)

    r_m, g_m, b_m = 0, 0, 0
    for w in range(img1.size[0]):
        for h in range(img1.size[1]):
            p1 = img1.getpixel((w, h))
            p2 = img2.getpixel((w, h))
            if p1 != p2:
                # for calculating the exact diff: abs(img1.getpixel((w, h)) - img2.getpixel((w, h)))
                r = abs(p1[0] - p2[0])
                r_m = max(r, r_m)
                g = abs(p1[1] - p2[1])
                g_m = max(g, g_m)
                b = abs(p1[2] - p2[2])
                b_m = max(b, b_m)
                if exact_diff:
                    diff.putpixel((w, h), (r, g, b))
                else:
                    diff.putpixel((w, h), (255, 255, 255))

    diff.save(output_path)
    print("The images differ with the maximum diffrence in each pixel RGB channel as:")
    print(f"R: {r_m} \nG: {g_m} \nB: {b_m}")


if __name__ == '__main__':
    show_diff("ves1.png", "out1.png", "RGB",
              "diff.png", True)
