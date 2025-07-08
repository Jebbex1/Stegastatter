class ContentWrapperError(Exception):
    pass


class TokenError(ContentWrapperError):
    pass


class SteganographyError(Exception):
    pass


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
