import multiprocessing
from typing import Generator, Any

from errors import BPCSError


def compute_segment_division_indices(total_length: int, segment_length: int) -> list[zip]:
    """
    Divides a range of length total_length into separate segments of all length segment_length. Leaves out any segments
    that don't have length of segment_length (if total_length%segment_length != 0 then we have segments that aren't of
    length segment_length).
    :param total_length: the length to divide
    :param segment_length: the length of each segment
    :return: a list of the starting and ending indices of each range in the form list[n] = (start, end)
    """
    startings = range(0, total_length, segment_length)
    endings = []
    for left in startings:
        end = min(total_length, left + segment_length)
        if end % segment_length == 0:
            endings.append(end)
    return list(zip(startings, endings))


def compute_all_block_indices(image_shape: tuple[int, int, int, int],
                              block_shape: tuple[int, int]) -> Generator[list[slice], Any, None]:
    """
    Computes every possible block location in an image of shape (x, y, channel, bit-plane index).
    :param image_shape: an array describing the image to compute all grid dimensions from
    :param block_shape: a tuple of two integers representing the size of each bit plane
    :return: A generator in which every item is in the form of:
     slice(x_start, x_end, None), slice(y_start, y_end, None), channel_num, bit_plane_index
    :raises BPCSError: if given an image object with an incorrect shape
    """
    update_logger = multiprocessing.get_logger()
    if len(image_shape) != 4:
        raise BPCSError(f"Image shape does not match: (width, height, channel number, bits per channel value). "
                        f"Given shape: {image_shape}")

    x_segments = compute_segment_division_indices(image_shape[0], block_shape[0])
    y_segments = compute_segment_division_indices(image_shape[1], block_shape[1])

    num_of_total_blocks = (image_shape[2] * image_shape[3] * len(x_segments) * len(y_segments))

    update_logger.info(f"Found {num_of_total_blocks} blocks of shape {block_shape} in the image.")

    i = 0
    for bit_index in reversed(range(image_shape[3])):  # each bit index from lsb -> msb
        for channel_index in range(image_shape[2]):  # each channel
            for (x_left, x_right) in x_segments:  # width
                for (y_left, y_right) in y_segments:  # height
                    i += 1
                    if i % 10000 == 0:
                        update_logger.info(f"Block #{i} of {num_of_total_blocks}")
                    yield [slice(x_left, x_right), slice(y_left, y_right)] + [channel_index, bit_index]
