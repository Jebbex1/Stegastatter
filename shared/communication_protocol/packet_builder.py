import shared.communication_protocol.packet_structure as structure


def build_header(name: str, value: str | int | float) -> bytes:
    """
    Builds a header line
    :param name: the name of the header we want to create
    :param value: the value of the header we want to create
    :return: the header line in str format
    """
    return name.encode() + b":" + str(value).encode() + structure.SEP


def build_packet(code: str, headers: dict[str, str] | None = None, body: bytes | None = None) -> bytes:
    """
    Builds a packet in the shared' structure
    :param body:
    :param code: the packets' code
    :param headers: the packets' headers (if any)
    :return: the packet in str format
    """
    code_line = code.encode() + b":" + structure.CODES[code][0].encode() + structure.SEP
    body = body if body is not None else b""
    if headers is None:
        return code_line + body + structure.END
    header_lines = b""
    for header, value in headers.items():
        header_lines += build_header(header, value)
    return code_line + header_lines + body + structure.END
