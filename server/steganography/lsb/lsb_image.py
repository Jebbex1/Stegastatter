import multiprocessing
from typing import Generator, Any

from PIL import Image

from server.steganography.image_utils import open_image_from_bytes
from server.steganography.lsb.lsb_errors import LSBCapacityError
from server.steganography.steganography_errors import SteganographyError

# Mask used to put one (ex:1->00000001, 2->00000010) associated with OR bitwise
TRUE_MASK_VALUES = [1, 2, 4, 8, 16, 32, 64, 128]

# Mask used to put zero (ex:254->11111110, 253->11111101) associated with AND bitwise
FALSE_MASK_VALUES = [254, 253, 251, 247, 239, 223, 191, 127]


class LSBImage:
    def __init__(self, image_bytes, sacrificed_bits=2):
        update_logger = multiprocessing.get_logger()
        update_logger.info("Loading image...")
        self.image = open_image_from_bytes(image_bytes)
        self.iv_bit_len = len(bin(self.image.width*self.image.height*len(self.image.getbands()) * sacrificed_bits)[2:])
        self.max_bits_per_byte = sacrificed_bits

        self.one_mask_values = TRUE_MASK_VALUES[:sacrificed_bits]
        self.one_mask_max = self.one_mask_values[-1]
        self.one_mask = self.one_mask_values.pop(0)

        self.zero_max_values = FALSE_MASK_VALUES[:sacrificed_bits]
        self.zero_mask_max = self.zero_max_values[-1]
        self.zero_mask = self.zero_max_values.pop(0)

        self.cursor_width = 0  # Current width position
        self.cursor_height = 0  # Current height position
        self.cursor_channel = 0  # Current channel position
        update_logger.info("Loaded Image!")

    def increment_cursor(self):
        if self.cursor_channel < len(self.image.getbands()) - 1:
            self.cursor_channel += 1
            return
        self.cursor_channel = 0

        if self.cursor_width < self.image.width - 1:
            self.cursor_width += 1
            return
        self.cursor_width = 0

        if self.cursor_height < self.image.height - 1:
            self.cursor_height += 1
            return
        self.cursor_height = 0

        if self.one_mask < self.one_mask_max:
            self.one_mask = self.one_mask_values.pop(0)
            self.zero_mask = self.zero_max_values.pop(0)
            return

        raise LSBCapacityError("No available slot remaining (image filled)")

    def put_binary_value(self, bits: list[bool] | Generator[bool, Any, None]):
        for bit in bits:
            pixel = list(self.image.getpixel((self.cursor_width, self.cursor_height)))
            byte_value = int(pixel[self.cursor_channel])
            if bit:
                pixel[self.cursor_channel] = byte_value | self.one_mask  # bitwise OR with one_mask
            else:
                pixel[self.cursor_channel] = byte_value & self.zero_mask  # bitwise AND with one_mask

            self.image.putpixel((self.cursor_width, self.cursor_height), tuple(pixel))
            self.increment_cursor()

    def read_bit(self) -> bool:
        value_byte = self.image.getpixel((self.cursor_width, self.cursor_height))[self.cursor_channel]
        value_byte = int(value_byte) & self.one_mask
        self.increment_cursor()
        if value_byte > 0:
            return True
        else:
            return False

    def read_bits(self, num_of_bits: int) -> list[bool]:
        bits = []
        for i in range(num_of_bits):
            bits.append(self.read_bit())
        return bits

    def read_byte(self) -> list[bool]:
        return self.read_bits(8)

    def encode(self, data: bytes, check_capacity: bool):
        update_logger = multiprocessing.get_logger()
        update_logger.info("Starting embedding process...")()
        # FIXME

        data_byte_length = len(data)

        if check_capacity:
            if not self.check_capacity(data_byte_length*8):
                raise LSBCapacityError("Carrier image not big enough to contain all the data to encode.")

        self.put_binary_value(binary_value(data_byte_length, self.iv_bit_len))
        for byte in data:
            self.put_binary_value(binary_value(byte, 8))

        update_logger.info("Finished embedding process!")
        return self.image

    def decode(self):
        update_logger = multiprocessing.get_logger()
        update_logger.info("Starting reading process...")

        # FIXME
        data_length = int(self.read_bits(self.iv_bit_len), 2)
        output = b""
        for i in range(data_length):
            output += bytearray([int(self.read_byte(), 2)])

        update_logger.info("Reading process finished!")
        return output

    def check_capacity(self, data_bit_length: int) -> bool:
        update_logger = multiprocessing.get_logger()
        update_logger.info("Calculating if sent data will fit into the image...")
        return ((self.image.width * self.image.height * len(self.image.getbands()) * self.max_bits_per_byte)
                < data_bit_length + self.iv_bit_len)


def binary_value(val, bit_num):  # Return the binary value of an int as a byte
    bin_value = bin(val)[2:]
    if len(bin_value) > bit_num:
        raise SteganographyError("binary value larger than the expected size")
    return bin_value.zfill(bit_num)


def bits(st: bytes) -> Generator[bool, Any, None]:
    bytes_gen = (b for b in st)
    for b in bytes_gen:
        for i in reversed(range(8)):
            yield bool((b >> i) & True)
