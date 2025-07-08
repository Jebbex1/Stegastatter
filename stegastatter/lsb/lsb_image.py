import multiprocessing
from math import log2, ceil
from typing import Generator, Any

from bit_operations_utils import bits_to_bytes, bit_list_to_int, bytes_to_bit_list, \
    bitlist_str_to_list
from image_utils import open_image_from_bytes
from errors import LSBError, LSBCapacityError

# Mask used to put one (ex:1->00000001, 2->00000010) associated with OR bitwise
TRUE_BIT_MASK_VALUES = [1, 2, 4, 8, 16, 32, 64, 128]

# Mask used to put zero (ex:254->11111110, 253->11111101) associated with AND bitwise
FALSE_BIT_MASK_VALUES = [254, 253, 251, 247, 239, 223, 191, 127]


def construct_iv(data_bit_length: int, iv_bit_length: int) -> list[bool]:
    iv = bitlist_str_to_list(bin(data_bit_length)[2:], iv_bit_length)
    iv = iv[:iv_bit_length]
    return iv


class LSBImage:
    def __init__(self, image_bytes, sacrificed_bits=2):
        update_logger = multiprocessing.get_logger()
        update_logger.info("Loading image...")
        self.image = open_image_from_bytes(image_bytes)
        self.iv_bit_len = ceil(log2(self.image.width*self.image.height*len(self.image.getbands())*sacrificed_bits))
        self.max_bits_per_byte = sacrificed_bits

        if not 0 < self.max_bits_per_byte <= 8:
            raise LSBError("The number of bits dedicated to storing data per byte must be 0 < num <= 8")

        self.one_mask_values = TRUE_BIT_MASK_VALUES[:sacrificed_bits]
        self.one_mask_max = self.one_mask_values[-1]
        self.one_mask = self.one_mask_values.pop(0)

        self.zero_max_values = FALSE_BIT_MASK_VALUES[:sacrificed_bits]
        self.zero_mask_max = self.zero_max_values[-1]
        self.zero_mask = self.zero_max_values.pop(0)

        self.cursor_width = 0  # Current width position
        self.cursor_height = 0  # Current height position
        self.cursor_channel = 0  # Current channel position
        update_logger.info("Loaded Image!")

    def increment_cursor(self):
        if self.cursor_width < self.image.width - 1:
            self.cursor_width += 1
            return
        self.cursor_width = 0

        if self.cursor_height < self.image.height - 1:
            self.cursor_height += 1
            return
        self.cursor_height = 0

        if self.cursor_channel < len(self.image.getbands()) - 1:
            self.cursor_channel += 1
            return
        self.cursor_channel = 0

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

    def embed(self, data: bytes, check_capacity: bool):
        update_logger = multiprocessing.get_logger()
        update_logger.info("Starting embedding process...")

        data_byte_length = len(data)

        if check_capacity:
            update_logger.info("Checking if image has enough capacity to contain the sent data...")
            if not self.check_capacity(data_byte_length*8):
                update_logger.info("Image does NOT have enough capacity!")
                raise LSBCapacityError("Carrier image not big enough to contain all the data to embed.")
            update_logger.info("Image has enough capacity!")

        iv_bits = construct_iv(data_byte_length*8, self.iv_bit_len)
        data_bits = bytes_to_bit_list(data)

        self.put_binary_value(iv_bits)
        self.put_binary_value(data_bits)

        update_logger.info("Finished embedding process!")

        return self.image

    def extract(self):
        update_logger = multiprocessing.get_logger()
        update_logger.info("Starting reading process...")

        iv = self.read_bits(self.iv_bit_len)
        data_length = bit_list_to_int(iv)
        output = self.read_bits(data_length)

        update_logger.info("Reading process finished!")
        return bits_to_bytes(output)

    def check_capacity(self, data_bit_length: int) -> bool:
        update_logger = multiprocessing.get_logger()
        update_logger.info("Calculating if sent data will fit into the image...")
        return ((self.image.width * self.image.height * len(self.image.getbands()) * self.max_bits_per_byte)
                >= data_bit_length + self.iv_bit_len)
