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
    return int("".join((str(int(i)) for i in bitlist)), 2)


def bytes_to_bit_list(st: bytes, length: int = None) -> list[bool]:
    bitlist = []
    bytes_gen = (b for b in st)
    for b in bytes_gen:
        for i in reversed(range(8)):
            bitlist.append(bool((b >> i) & True))
    if length is not None:
        bitlist = (max(length - len(bitlist), 0) * [False]) + bitlist
    return bitlist


def bitlist_str_to_list(bitlist_str: str, length: int):
    bitlist = list(bool(int(i)) for i in bitlist_str)
    bitlist = (max(length - len(bitlist), 0) * [False]) + bitlist
    return bitlist
