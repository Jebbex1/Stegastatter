import multiprocessing
import numpy as np

from server.steganography.bpcs.dimension_computing import compute_all_block_indices
from server.steganography.bpcs.block_operations import blocks_to_bits
from server.steganography.bit_operations_utils import bits_to_bytes
from server.steganography.bpcs.bpcs_errors import BPCSExtractError
from server.steganography.bpcs.core import calc_bpcs_complexity_coefficient, conjugate
from server.steganography.bpcs.initilization_vector import slice_iv_from_accepted_blocks, \
    slice_conj_blocks_from_accepted_blocks


def get_extracting_info_from_accepted_blocks(accepted_blocks: np.ndarray, block_shape: tuple[int, int],
                                             alpha: float) -> tuple[int, int, list[bool], np.ndarray]:
    """
    Extract the extracting info (iv values, conjugation map) from the accepted blocks. This function assumes that the
    relevant blocks start at index = 0 of the block array.
    :param accepted_blocks: the accepted blocks in the vessel image
    :param block_shape: the shape of each bit plane block in the image
    :param alpha: the minimum complexity coefficient of the blocks
    :return: the extracting info with the remaining blocks in the form of: message_block_length, message_remnant_bits_num,
    conjugation_map, remaining_blocks
    """
    (message_block_length, message_remnant_bits_num), remaining_blocks = (
        slice_iv_from_accepted_blocks(accepted_blocks, block_shape, alpha))

    conjugation_map, remaining_blocks = slice_conj_blocks_from_accepted_blocks(remaining_blocks, block_shape, alpha,
                                                                               message_block_length)
    return message_block_length, message_remnant_bits_num, conjugation_map, remaining_blocks


def extract_message_from_remaining_blocks(remaining_blocks: np.ndarray, message_block_length: int,
                                          message_remnant_bits_num: int, conjugation_map: list[bool],
                                          block_shape: tuple[int, int]) -> bytes:
    """
    Extracts the message from the image bit plane blocks, using the data from the iv blocks, and the conjugation map.
    This function assumes that the start of the message blocks is at index = 0 of the remaining blocks
    :param remaining_blocks: the remaining blocks in the image after slicing the iv and conj map blocks
    :param message_block_length: the bit length of the message we want to extract in bits
    :param message_remnant_bits_num: the number of bits that belong to the message in the last message block
    :param conjugation_map: a list of bools describing what message blocks were conjugated
    :param block_shape: the shape of each bit plane block in the image
    :return: the extracted message in bytes
    """
    block_area = block_shape[0] * block_shape[1]
    message_blocks = []
    try:
        for i in range(message_block_length):
            block = remaining_blocks[i]
            if conjugation_map[i]:
                message_blocks.append(conjugate(block))
            else:
                message_blocks.append(block)
    except IndexError:
        # this can only happen when the block length extracted from the image is incorrect, this must be caused by an
        # incorrect minimum complexity coefficient. Which means that the client sent an image-token pair that didn't
        # match
        raise BPCSExtractError("The supplied token and image dont match each other. This might happen when opening the "
                               "token with a text editor.")

    message_bits = blocks_to_bits(np.array(message_blocks))
    message_bits = message_bits[:len(message_bits) - (block_area - message_remnant_bits_num)]

    return bits_to_bytes(message_bits)


def extract_message_from_vessel(vessel_blocks: np.ndarray, alpha: float, block_shape: tuple[int, int]) -> bytes:
    """
    Given an array of vessel blocks in the image, extract the iv and conjugation map blocks, and use them to extract the
    message from the remaining blocks.
    :param vessel_blocks: the images' bit plane blocks
    :param alpha: the minimum complexity coefficient threshold to decide which blocks to accept
    :param block_shape: the shape of each bit plane block in the image
    :return: the extracted message in bytes
    :raises BPCSExtractError: if there is a mismatch between the iv, conj map, and image blocks info
    """
    update_logger = multiprocessing.get_logger()
    update_logger.info("Starting reading process...")
    accepted_blocks = []
    bit_planes = compute_all_block_indices(vessel_blocks.shape, block_shape)

    update_logger.info("Extracting blocks with an appropriate complexity coefficient from image blocks...")
    # get all accepted blocks (every block that has a >= alpha0)
    for bit_plane in bit_planes:
        block = vessel_blocks[tuple(bit_plane)]
        if calc_bpcs_complexity_coefficient(block) >= alpha:
            accepted_blocks.append(block)

    accepted_blocks = np.reshape(accepted_blocks, (len(accepted_blocks),) + block_shape)

    update_logger.info("Extracting initialization vector and conjugation map blocks from accepted blocks...")
    message_block_length, message_remnant_bits_num, conjugation_map, remaining_blocks = (
        get_extracting_info_from_accepted_blocks(accepted_blocks, block_shape, alpha))

    if len(remaining_blocks) < message_block_length:
        raise BPCSExtractError(f"The message block length iv states that the number of message blocks in the image is "
                               f"{message_block_length} but there are only {len(remaining_blocks)} blocks. "
                               f"{message_block_length} < {len(remaining_blocks)}")

    if message_remnant_bits_num > block_shape[0] * block_shape[1]:
        raise BPCSExtractError(f"The message remnant bits number states that the number of bits that belong to the "
                               f"message in a block of total length {block_shape[0] * block_shape[1]} is "
                               f"{message_remnant_bits_num}, this is not possible since the message can only take "
                               f"{block_shape[0] * block_shape[1]} bits per block. Not more.")

    update_logger.info("Using extracing info to extract message from accepted blocks...")
    message = extract_message_from_remaining_blocks(remaining_blocks, message_block_length, message_remnant_bits_num,
                                                    conjugation_map, block_shape)
    update_logger.info("Reading process finished!")
    return message
