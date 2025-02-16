import io
import PIL
import PIL.Image

from shared.communication_protocol.communication_errors import PacketContentsError


def open_image_from_bytes(image_bytes: bytes) -> PIL.Image.Image:
    try:
        return PIL.Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except PIL.UnidentifiedImageError:
        raise PacketContentsError("Expected image bytes, got otherwise")