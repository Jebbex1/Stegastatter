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


class LSBEncodeError(LSBError):
    """
    Errors that deal with the encoding process of data in an image.
    """
    pass


class LSBDecodeError(LSBError):
    """
    Errors that deal with the decoding process of data in an image.
    """
    pass
