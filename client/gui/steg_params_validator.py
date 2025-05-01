from client.gui.gui_errors import InvalidParameters


def validate_ecc_params(block_size: str, symbol_num: str):
    try:
        block_size, symbol_num = int(block_size), int(symbol_num)
        if not 0 < block_size <= 255:
            raise InvalidParameters("Block size must be greater than 0 and less or equal to 255.")
        if not 0 <= symbol_num <= 0.5 * block_size:
            raise InvalidParameters("Symbol number must be between or equal to 0 and half of the block size.")
    except ValueError:
        raise InvalidParameters("Block size and symbol number must be integers.")


def validate_bpcs_params(min_alpha: str):
    try:
        min_alpha = float(min_alpha)
        if not 0 <= min_alpha <= 0.5:
            raise InvalidParameters("Minimum complexity coefficient must be between or equal to 0 and 0.5.")
    except ValueError:
        raise InvalidParameters("Minimum complexity coefficient must be a floating point number.")


def validate_lsb_params(num_of_sacrificed_bits: str):
    try:
        num_of_sacrificed_bits = int(num_of_sacrificed_bits)
        if not 0 < num_of_sacrificed_bits <= 8:
            raise InvalidParameters("Number of sacrificed bits must be greater than 0 and less or equal to 8.")
    except ValueError:
        raise InvalidParameters("Number of sacrificed bits must be an integer.")
