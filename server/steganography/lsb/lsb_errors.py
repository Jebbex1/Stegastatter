from server.steganography.steganography_errors import SteganographyError


class LSBError(SteganographyError):
    """
    The parent error of all LSB related errors.
    """
    pass


class LSBCapacityError(LSBError):
    """
    Errors that deal with the capacity of an image.
    """
    pass


class LSBEmbedError(LSBError):
    """
    Errors that deal with the embedding process of data in an image.
    """
    pass


class LSBExtractError(LSBError):
    """
    Errors that deal with the extracting process of data in an image.
    """
    pass
