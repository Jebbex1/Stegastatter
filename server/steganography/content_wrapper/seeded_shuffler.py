import random
import numpy


def get_shuffled_perm(length: int, seed: bytes):
    perm = list(numpy.arange(length) + 1)
    random.seed(seed)
    random.shuffle(perm)
    return perm


def shuffle_bytes(raw_bytes: bytes, seed: bytes):
    # Shuffle the list ls using the seed `seed`
    raw_bytes = bytearray(raw_bytes)
    random.seed(seed)
    random.shuffle(raw_bytes)
    return bytes(raw_bytes)


def unshuffle_bytes(shuffled_bytes: bytes, seed: bytes):
    shuffled_perm = get_shuffled_perm(len(shuffled_bytes), seed)

    zipped_ls = list(zip(shuffled_bytes, shuffled_perm))
    zipped_ls.sort(key=lambda x: x[1])
    unshuffled = bytearray()
    [unshuffled.append(a) for (a, b) in zipped_ls]
    return bytes(unshuffled)
