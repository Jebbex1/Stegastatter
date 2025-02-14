import errors


class BPCSError(errors.SteganographyError):
    """
    The parent error of all BPCS related errors.
    """
    pass


class BPCSCapacityError(BPCSError):
    """
    Errors that deal with the capacity of an image.
    """
    pass


class BPCSEncodeError(BPCSError):
    """
    Errors that deal with the encoding process of data in an image.
    """
    pass


class BPCSDecodeError(BPCSError):
    """
    Errors that deal with the decoding process of data in an image.
    """
    pass
