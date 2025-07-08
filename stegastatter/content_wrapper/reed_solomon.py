from reedsolo import RSCodec, ReedSolomonError


def pad(content: bytes, ecc_block_size: int, ecc_symbol_num: int) -> bytes:
    """
    Pads content with Reed-Solomon Error Correction Codes.
    :param content: the content to be padded
    :param ecc_block_size: the rs block size
    :param ecc_symbol_num: the bytes per block that we want to dedicate for error correction
    :return: the padded content
    :raises ReedSolomonError: if the function was fed invalid parameters
    """
    if ecc_symbol_num == 0:
        return content

    if ecc_block_size > 255:
        # According to the reedsolo docs, if the block size is larger than 255, complexity and computational cost goes
        # up quadratically. So we limit the maximum block size to be 255.
        raise ReedSolomonError(f"Block size is too large: {ecc_block_size}")
    if ecc_symbol_num >= ecc_block_size:
        raise ReedSolomonError(f"ECC Symbol num is larger than the block size: {ecc_symbol_num} > {ecc_block_size}")
    rsc = RSCodec(ecc_symbol_num, nsize=ecc_block_size)
    return bytes(rsc.encode(content))


def unpad(padded: bytes, block_size: int, ecc_symbol_num: int) -> bytes:
    """
    Unpads padded content with Reed-Solomon Error Correction Codes.
    :param padded: the padded content
    :param block_size: the rs block size
    :param ecc_symbol_num: the bytes per block that we want to dedicate for error correction
    :return: the unpadded content
    :raises ReedSolomonError: if the function was fed invalid parameters, or the data had too many errors for the rs
    algorithm to fix.
    """
    if ecc_symbol_num == 0:
        return padded

    if block_size > 255:
        # According to the reedsolo docs, if the block size is larger than 255, complexity and computational cost goes
        # up quadratically. So we limit the maximum block size to be 255.
        raise ReedSolomonError(f"Block size is too large: {block_size}")
    if ecc_symbol_num >= block_size:
        raise ReedSolomonError(f"ECC Symbol num is larger than the block size: {ecc_symbol_num} > {block_size}")
    rsc = RSCodec(ecc_symbol_num, nsize=block_size)
    return rsc.decode(padded)[0]
