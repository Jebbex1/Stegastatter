import multiprocessing
import numpy as np

from server.steganography.bpcs.block_operations import bytes_to_blocks
from server.steganography.bpcs.core import calc_bpcs_complexity_coefficient, conjugate
from server.steganography.bpcs.initilization_vector import build_iv_blocks, build_conjugation_blocks
from server.steganography.bpcs.bpcs_errors import BPCSError, BPCSCapacityError
from server.steganography.bpcs.capacity import calculate_embedding_blocks_num, collect_accepted_blocks


def get_message_blocks_from_bytes(message: bytes) -> tuple[np.ndarray, int]:
    """
    Constructs message blocks from given bytes.
    :param message: the message bytes
    :return: the message blocks derived from the given bytes, and the bit length of the message blocks
    """
    return bytes_to_blocks(message, (8, 8)), len(message) * 8


def get_conjugated_blocks_and_data(blocks: np.ndarray) -> tuple[np.ndarray, list[bool]]:
    """
    Given an array of blocks, iterate over them and conjugate them if needed, and record the conjugation operations in a
    conjugation map. This function uses 0.5 as the threshold for conjugation instead of alpha0, to increase the noise
    of the conjugation map.
    :param blocks: the array of blocks
    :return: the mapped blocks, with their matching conjugation map
    """
    conjugation_map = []
    i = 0
    for block in blocks:
        if calc_bpcs_complexity_coefficient(block) >= 0.5:
            conjugation_map.append(False)
        else:
            conjugation_map.append(True)
            blocks[i] = conjugate(block)
        i += 1
    return blocks, conjugation_map


def embed_message_in_vessel(vessel_blocks: np.ndarray, alpha: float, message_blocks: np.ndarray,
                            message_bit_length: int, block_shape: tuple[int, int], check_capacity) -> np.ndarray:
    """
    Embeds an array of given message blocks and a given bit length into given vessel blocks.
    :param check_capacity: should we check the capacity of the vessel blocks before starting modify the vessel blocks?
    :param vessel_blocks: the blocks to embed the message into
    :param alpha: the minimum complexity coefficient threshold for each block, so that we know which bit plane blocks
    to modify in the vessel blocks.
    :param message_blocks: the message blocks to embed into the vessel blocks
    :param message_bit_length: the length of the message in bits
    :param block_shape: the shape for each block in the given array of message_blocks
    :return: the vessel blocks after embedding the message into them
    :raises BPCSError: if given an incorrect complexity coefficient threshold
    :raises BPCSCapacityError: if the vessel blocks don't have enough capacity to embed all the needed data
    """
    update_logger = multiprocessing.get_logger()
    update_logger.info("Starting embedding process...")

    if not 0 <= alpha <= 0.5:
        raise BPCSError("The minimum complexity coefficient must be between 0 and 0.5")

    update_logger.info("Counting accepted blocks number...")
    accepted_blocks_coords = collect_accepted_blocks(vessel_blocks, vessel_blocks.shape, block_shape, alpha)

    if check_capacity:
        update_logger.info("Checking image capacity...")
        if calculate_embedding_blocks_num(len(accepted_blocks_coords), block_shape, alpha,
                                          message_bit_length) <= len(accepted_blocks_coords):
            update_logger.info("Image has enough capacity of the embedding data!")
        else:
            update_logger.warning("Image does not have enough capacity of the embedding data!")
            raise BPCSCapacityError("Image does not have enough capacity of the embedding data")

    update_logger.info("Building initialization vector blocks...")
    iv_blocks = build_iv_blocks(len(accepted_blocks_coords), block_shape, alpha, message_bit_length)

    update_logger.info("Building conjugation map blocks...")
    message_blocks, conj_map = get_conjugated_blocks_and_data(message_blocks)

    conjugation_blocks = build_conjugation_blocks(conj_map, block_shape, alpha)

    embedding_blocks = np.concatenate([iv_blocks, conjugation_blocks, message_blocks])

    update_logger.info(f"Embedding {len(embedding_blocks)} blocks in image blocks...")

    embedding_block_index = 0
    for block_coords in accepted_blocks_coords:
        if embedding_block_index >= len(embedding_blocks):
            break

        vessel_blocks[tuple(block_coords)] = embedding_blocks[embedding_block_index]
        embedding_block_index += 1

        if embedding_block_index % 10000 == 0:
            update_logger.info(f"Block #{embedding_block_index} of {len(embedding_blocks)}")

    if embedding_block_index < len(embedding_blocks):
        raise BPCSCapacityError("Image does not have enough capacity of the embedding data!")

    update_logger.info("Finished embedding process!")
    return vessel_blocks
