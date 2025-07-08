import itertools
import multiprocessing
from typing import Generator, Callable
import numpy as np

from errors import BPCSError


def xor_lists(a: list[bool], b: list[bool]) -> list[bool]:
    """
    Given two lists a and b, xor every Nth element in each list and put the results in a list.
    :param a: list #1
    :param b: list #2
    :return: a list containing the XOR-ed values of the two lists
    :raises BPCSError: if given two lists of different length
    """
    if len(a) != len(b):
        raise BPCSError(f"Length of given lists to XOR does not match. {len(a)} != {len(b)}")
    return [x ^ y for x, y in zip(a, b)]


def map_2d_array(arr: np.ndarray, func: Callable) -> np.ndarray:
    """
    Given a 2d numpy array, and a function func, map over each and every element of arr while reassigning it to
    func(arr[i, j]), and returning the resulting 2d numpy array.
    :param arr: 2d numpy array
    :param func: a function
    """
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            arr[i, j] = func(arr[i, j])
    return arr


def pbc_to_cgc(pixels: np.ndarray) -> np.ndarray:
    """
    Converts pixels from PBC to CGC, the process for this is detailed as such:
    The first bit allways matches, for the rest of the bits we do g[i] = b[i] XOR b[i-1]
    :param pixels: an array describing the pixels that uses PBC to represent values
    :return: an array of pixels that uses CGC to represent values instead of PBC
    """
    update_logger = multiprocessing.get_logger()
    update_logger.info("Converting values from PBC to CGC...")

    def pbc_to_cgc_mapper(planes):
        new_planes = []
        for i in range(planes.shape[1]):
            if i == 0:
                new_planes.append(planes[:, i].tolist())
            else:
                new_planes.append(xor_lists(planes[:, i], planes[:, i - 1]))
        return np.array(new_planes).transpose()

    return map_2d_array(pixels, pbc_to_cgc_mapper)


def cgc_to_pbc(arr: np.ndarray) -> np.ndarray:
    """
    Converts pixels from CGC to PBC, the process for this is detailed as such:
    The first bit allways matches, for the rest of the bits we do b[i] = g[i] XOR b[i-1]
    :param arr: n array of pixels that uses CGC to represent values
    :return: an array of pixels that uses PBC to represent values instead of CGC
    """
    update_logger = multiprocessing.get_logger()
    update_logger.info("Converting values from CGC to PBC...")

    def cgc_to_pbc_mapper(planes):
        new_planes = []
        for i in range(planes.shape[1]):
            if i == 0:
                new_planes.append(planes[:, i].tolist())
            else:
                new_planes.append(xor_lists(planes[:, i], new_planes[i - 1]))
        return np.array(new_planes).transpose()

    return map_2d_array(arr, cgc_to_pbc_mapper)


def bit_list_to_decimal(bits: list[bool]) -> int:
    """
    Convert a given list of singular bits to a decimal value.
    :param bits: the list of bits
    :return: the converted decimal value
    """
    return int(''.join(["1" if x else "0" for x in bits]), 2)


def decimal_to_bit_list(val: int, bit_num: int) -> list[bool]:
    """
    Convert a given decimal value to a list of bits with a given length.
    :param val: the decimal value
    :param bit_num: the number of bits that the bit list should contain
    :return: the converted list of bits
    """
    return [bool(i) for i in [int(x) for x in bin(val)[2:].zfill(bit_num)[:bit_num]]]


class BitPlane:
    """
    The class that manages conversion from Pure Binary Code to Canonical Gray Code and back.
    """
    def __init__(self, pixel_array: np.ndarray, gray=True):
        """
        Initializes a BitPlane object.
        :param pixel_array: an array that describes the pixels of an image
        :param gray: should the array be read in CGC instead of PBC.
        """
        self.arr = pixel_array
        self.gray = gray

    def slice(self) -> np.ndarray:
        """
        Converts the values in self.arr into binary, so that every element in i,j now contains a bit-list that
        describes the decimal value instead the decimal value itself; every binary value has bit_num bits. Also,
        converts the self.arr into CGC if self.gray is True.
        Keeps the shape of self.arr.
        :return: the converted numpy ndarray
        """
        update_logger = multiprocessing.get_logger()
        update_logger.info("Slicing image into bit plane blocks...")

        # reshape to a 1d list binary bit vals
        base_array = np.array([decimal_to_bit_list(i, 8) for i in self.arr.reshape(-1)])

        # reshape back to the same shape as the og array with an added dimension for the bit list
        temp_array = np.reshape(base_array, self.arr.shape + (8,))
        if self.gray:
            temp_array = pbc_to_cgc(temp_array)
        return temp_array

    def stack(self) -> np.ndarray:
        """
        Does the reverse of slicing; converts self.arr to decimal values, so that every element in i,j now contains
        a decimal value instead of a bit-list. Also, converts self.arr back to PBC if self.gray is True. Keeps the
        shape of self.arr.
        """
        update_logger = multiprocessing.get_logger()
        temp_array = self.arr
        if self.gray:
            temp_array = cgc_to_pbc(temp_array)

        def iterate_all_but_last_dim(arr: np.ndarray) -> Generator:
            all_indices = [range(dim_size) for dim_size in arr.shape]
            for ind in itertools.product(*all_indices[:-1]):
                yield ind

        update_logger.info("Stacking bit plane blocks into an image...")
        temp_array = np.reshape([bit_list_to_decimal(temp_array[ind]) for ind in iterate_all_but_last_dim(temp_array)],
                                temp_array.shape[:-1])
        return temp_array
