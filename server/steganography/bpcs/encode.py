import numpy as np

from bpcs.block_operations import bytes_to_blocks
from bpcs.dimension_computing import compute_all_block_indices
from bpcs.core import calc_bpcs_complexity_coefficient, conjugate
from bpcs.initilization_vector import build_iv_blocks, build_conjugation_blocks
from bpcs.bpcs_errors import BPCSError, BPCSCapacityError
from bpcs.capacity import calculate_embedding_blocks_num, count_accepted_blocks


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
    print("Starting embedding process...")

    if not 0 <= alpha <= 0.5:
        raise BPCSError('The minimum complexity coefficient must be between 0 and 0.5')

    print("Counting accepted blocks number...")
    accepted_blocks_num = count_accepted_blocks(vessel_blocks, vessel_blocks.shape, block_shape, alpha)

    if check_capacity:
        print("Checking image capacity...")
        if calculate_embedding_blocks_num(accepted_blocks_num, block_shape, alpha,
                                          message_bit_length) <= accepted_blocks_num:
            print("Image has enough capacity of the embedding data!")
        else:
            print("Image does not have enough capacity of the embedding data.")
            raise BPCSCapacityError("Image does not have enough capacity of the embedding data!")

    print("Building initialization vector blocks...")
    iv_blocks = build_iv_blocks(accepted_blocks_num, block_shape, alpha, message_bit_length)

    print("Building conjugation map blocks...")
    message_blocks, conj_map = get_conjugated_blocks_and_data(message_blocks)

    conjugation_blocks = build_conjugation_blocks(conj_map, block_shape, alpha)

    embedding_blocks = np.concatenate([iv_blocks, conjugation_blocks, message_blocks])

    print("Embedding blocks in image blocks")
    embedding_block_index = 0
    bit_plane_dims = compute_all_block_indices(vessel_blocks.shape, block_shape)
    for bit_plane in bit_plane_dims:
        if embedding_block_index >= len(embedding_blocks):
            break
        if calc_bpcs_complexity_coefficient(vessel_blocks[tuple(bit_plane)]) < alpha:
            continue

        vessel_blocks[tuple(bit_plane)] = embedding_blocks[embedding_block_index]
        embedding_block_index += 1

    if embedding_block_index < len(embedding_blocks):
        raise BPCSCapacityError("Image does not have enough capacity of the embedding data!")

    print("Finished embedding process!")
    return vessel_blocks
