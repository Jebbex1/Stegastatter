from typing import Generator, Any

import numpy as np


def bits_to_bytes(bits: list[bool]) -> bytes:
    """
    Converts a list of bits into bytes.
    :param bits: the given list of bits
    :return: a bytes type value, representing the value of the list of bits
    """
    spare_bits_length = len(bits) % 8  # calculate the length of any spare bits

    # since the message was initially read by the byte, any spares must have been added to create a block
    bits = bits[:len(bits) - spare_bits_length]  # get rid of any spare bits

    bytes_number = int(len(bits) / 8)
    message_bytes = np.resize(np.array(bits), [bytes_number, 8])

    def byte_to_decimal_int(byte: np.ndarray) -> int:
        return int('0b' + ''.join(str(int(x)) for x in byte.tolist()), 2)

    def decimal_int_to_bytes(byte) -> bytes:
        return byte_to_decimal_int(byte).to_bytes()

    return b''.join([decimal_int_to_bytes(byte) for byte in message_bytes])


def bit_list_to_int(bitlist: list[bool]) -> int:
    out = 0
    for bit in bitlist:
        out = (out << 1) | bit
    return out


def bytes_to_bit_list(st: bytes) -> Generator[bool, Any, None]:
    bytes_gen = (b for b in st)
    for b in bytes_gen:
        for i in reversed(range(8)):
            yield bool((b >> i) & True)
