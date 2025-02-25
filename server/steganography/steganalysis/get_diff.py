import io
import multiprocessing

from PIL import Image

from shared.communication_protocol.communication_errors import PacketContentsError
from server.steganography.image_utils import open_image_from_bytes


def show_diff(img1_bytes: bytes, img2_bytes: bytes, exact_diff: bool) -> tuple[tuple[int, int, int], bytes]:
    update_logger = multiprocessing.get_logger()

    update_logger.info("Loading images...")

    img1 = open_image_from_bytes(img1_bytes)
    img2 = open_image_from_bytes(img2_bytes)

    if img1.size != img2.size:
        raise PacketContentsError("Sent images must have same size")

    diff_image = Image.new("RGB", img1.size)

    update_logger.info("Calculating diffrences between the images...")

    r_diff, g_diff, b_diff = 0, 0, 0
    diff_pixels_num = 0
    for w in range(img1.size[0]):
        for h in range(img1.size[1]):
            p1 = img1.getpixel((w, h))
            p2 = img2.getpixel((w, h))

            if p1 != p2:
                diff_pixels_num += 1

                r = abs(p1[0] - p2[0])
                g = abs(p1[1] - p2[1])
                b = abs(p1[2] - p2[2])

                r_diff = max(r, r_diff)
                g_diff = max(g, g_diff)
                b_diff = max(b, b_diff)
                if exact_diff:
                    diff_image.putpixel((w, h), (r, g, b))
                else:
                    diff_image.putpixel((w, h),
                                        tuple(255 if d != 0 else 0 for d in (r, g, b)))
    update_logger.info(f"Found {diff_pixels_num} different pixels")

    image_bytes = io.BytesIO()
    diff_image.save(image_bytes, format="PNG")
    return (r_diff, g_diff, b_diff), image_bytes.getvalue()
