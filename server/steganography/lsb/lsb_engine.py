from PIL import Image


ONE_MASK_VALUES = [1, 2, 4, 8, 16, 32, 64, 128]
# Mask used to put one ex:1->00000001, 2->00000010 . associated with OR bitwise

ZERO_MASK_VALUES = [254, 253, 251, 247, 239, 223, 191, 127]
# Mak used to put zero ex:254->11111110, 253->11111101 . associated with AND bitwise


class StegError(Exception):
    pass


def binary_value(val, bit_num):  # Return the binary value of an int as a byte
    bin_value = bin(val)[2:]
    if len(bin_value) > bit_num:
        raise StegError("binary value larger than the expected size")
    return bin_value.zfill(bit_num)


class LSB:
    def __init__(self, im: Image.Image, max_bits_per_byte=2):
        self.image = im
        self.iv_bit_len = len(bin(im.width * im.height * len(im.getbands()) * max_bits_per_byte)[2:])
        self.max_bits_per_byte = max_bits_per_byte

        self.one_mask_values = ONE_MASK_VALUES[:max_bits_per_byte]
        self.one_mask_max = self.one_mask_values[-1]
        self.one_mask = self.one_mask_values.pop(0)

        self.zero_max_values = ZERO_MASK_VALUES[:max_bits_per_byte]
        self.zero_mask_max = self.zero_max_values[-1]
        self.zero_mask = self.zero_max_values.pop(0)

        self.curr_width = 0  # Current width position
        self.curr_height = 0  # Current height position
        self.curr_channel = 0  # Current channel position

    def next_slot(self):
        if self.curr_channel < len(self.image.getbands()) - 1:
            self.curr_channel += 1
            return
        self.curr_channel = 0

        if self.curr_width < self.image.width - 1:
            self.curr_width += 1
            return
        self.curr_width = 0

        if self.curr_height < self.image.height - 1:
            self.curr_height += 1
            return
        self.curr_height = 0

        if self.one_mask < self.one_mask_max:
            self.one_mask = self.one_mask_values.pop(0)
            self.zero_mask = self.zero_max_values.pop(0)
            return

        raise StegError("No available slot remaining (image filled)")

    def put_binary_value(self, bits: str):
        for c in bits:
            pixel = list(self.image.getpixel((self.curr_width, self.curr_height)))
            byte_value = int(pixel[self.curr_channel])
            if int(c) == 1:
                pixel[self.curr_channel] = byte_value | self.one_mask  # bitwise OR with one_mask
            else:
                pixel[self.curr_channel] = byte_value & self.zero_mask  # bitwise AND with one_mask

            self.image.putpixel((self.curr_width, self.curr_height), tuple(pixel))
            self.next_slot()

    def read_bit(self):
        val = self.image.getpixel((self.curr_width, self.curr_height))[self.curr_channel]
        val = int(val) & self.one_mask
        self.next_slot()
        if val > 0:
            return "1"
        else:
            return "0"

    def read_bits(self, nb):
        bits = ""
        for i in range(nb):
            bits += self.read_bit()
        return bits

    def read_byte(self):
        return self.read_bits(8)

    def encode_binary(self, data: bytes):
        data_length = len(data)
        if ((self.image.width * self.image.height * len(self.image.getbands())) * self.max_bits_per_byte
                < data_length * 8 + self.iv_bit_len):
            raise StegError("Carrier image not big enough to hold all the datas to steganography")
        self.put_binary_value(binary_value(data_length, self.iv_bit_len))
        for byte in data:
            self.put_binary_value(binary_value(byte, 8))
        return self.image

    def decode_binary(self):
        data_length = int(self.read_bits(self.iv_bit_len), 2)
        output = b""
        for i in range(data_length):
            output += bytearray([int(self.read_byte(), 2)])
        return output


if __name__ == '__main__':
    lsb = LSB(Image.open('../../../assets/test.png'), 8)

    # lsb.encode_binary(b"hello there")
    # lsb.image.save("output1.png")

    lsb1 = LSB(Image.open('../output1.png'), 8)
    print(lsb1.decode_binary())
