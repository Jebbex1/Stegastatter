IMAGE_MAX_WIDTH = 2560
IMAGE_MAX_HEIGHT = 1440


class SteganographyError(Exception):
    pass


class ContentWrapperError(Exception):
    pass


class ImageTooBigError(SteganographyError):
    pass
