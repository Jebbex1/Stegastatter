import numpy as np


def max_bpcs_complexity(row_num: int, col_num: int) -> int:
    """
    Calculate the maximum BPCS complexity of a bit plane given its size. Using the formula for a plane of size m, n:
    max_comp = m(n-1) + n(m-1)
    :param row_num: grids' number of columns
    :param col_num: grids' number of rows
    :return: the maximum BPCS complexity of the given bit plane
    """
    return ((col_num - 1) * row_num) + ((row_num - 1) * col_num)


def calculate_bit_changes(bits: list[bool]) -> int:
    """
    Calculate the number of bit changes in a given list of bits.
    :param bits: the given collection of bits
    :return: the number of bit changes
    """
    return sum([int(bits[i] ^ bits[i - 1]) for i in range(1, len(bits))])


def calc_bpcs_complexity_coefficient(bit_plane: np.ndarray) -> float:
    """
    Calculate the BPCS complexity coefficient of a given bit plane.
    :param bit_plane: the bit plane
    :return: the BPCS complexity coefficient of the given bitmap
    """
    max_complexity = max_bpcs_complexity(bit_plane.shape[0], bit_plane.shape[1])
    k = 0
    for row in bit_plane:
        k += calculate_bit_changes(row)
    for col in bit_plane.transpose():
        k += calculate_bit_changes(col)
    return (k * 1.0) / max_complexity


def checkerboard(h: int, w: int) -> np.ndarray:
    """
    Build a bit plane checkerboard of height h and width w
    :param h: wanted height
    :param w: wanted width
    :return: a checkerboard array of shape == [h,w]
    """
    re = np.r_[int(w / 2) * [False, True] + ([False] if w % 2 else [])]
    ro = True ^ re
    return np.vstack(int(h / 2) * (re, ro) + ((re,) if h % 2 else ()))


def conjugate(bit_plane: np.ndarray) -> np.ndarray:
    """
    Conjugates a given bit plane so that its complexity coefficient is 1-a where 'a' is the complexity coefficient of
    the given bit plane.
    :param bit_plane: the given bit plane
    :return: the conjugated bit plane
    """
    wc = checkerboard(bit_plane.shape[0], bit_plane.shape[1])  # white pixel at origin
    bc = True ^ wc  # black pixel at origin
    return np.array([[wc[i, j] if bit_plane[i, j] else bc[i, j] for j, cell in enumerate(row)]
                     for i, row in enumerate(bit_plane)])
