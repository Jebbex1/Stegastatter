from server.steganography.steganography_errors import SteganographyError


class BPCSError(SteganographyError):
    """
    The parent error of all BPCS related errors.
    """
    pass


class BPCSCapacityError(BPCSError):
    """
    Errors that deal with the capacity of an image.
    """
    pass


class BPCSEmbedError(BPCSError):
    """
    Errors that deal with the embedding process of data in an image.
    """
    pass


class BPCSExtractError(BPCSError):
    """
    Errors that deal with the extracting process of data in an image.
    """
    pass
