import re

from shared.communication_protocol.packet_structure import CODES, SEP, END, MAX_FILE_SIZE, MAX_FIELD_SIZE, \
    MAX_TITLE_SIZE
from shared.communication_protocol.communication_errors import PacketContentsError, PacketStructureError
from shared.communication_protocol.transmission import CHARSET

HEADER_PATTERN = r"([\w-]+:[\x20-\x7E]+\x1D\x0D)"

# a regex that matches any correctly structured packets (does not check packet parameters, only its structure)
PACKET_PATTERN = (
    r"^("  # starts with 
    r"(\d{3}:[\w\x20]+\x1D\x0D)"  # code and description
    fr"{HEADER_PATTERN}*"  # headers (zero or more)
    r")"
    
    r"[\x00-\xFF]*"  # body
    r"(\x04)$"  # ends with EOT
    # \x20-\x7E represents eve ascii character between space and ~
).encode()


def is_valid_packet_structure(content: bytes) -> bool:
    """
    Checks if a packets structure is correct.
    :param content: the string to check
    :return: True if the string matches the structures' RegEx pattern, False otherwise
    """
    try:
        return re.search(PACKET_PATTERN, content).string is not None
    except AttributeError:
        return False


def get_packet_code(packet: bytes) -> tuple[str, str]:
    """
    Gets the packet code and description from the raw packet string
    :param packet: the raw packet string
    :return: <packet code>,<packet string>
    """
    code_parts = packet.split(SEP)[0].split(b":")
    return code_parts[0].decode(), code_parts[1].decode()


def get_headers_dict(packet: bytes) -> dict[str, str]:
    """
    Gets the headers of the packet, and parses them into a dictionary
    :param packet: the raw packet string
    :return: a dictionary of the packet headers,  dict key -> header name and dict value -> header value
    """
    header_num = len(CODES[get_packet_code(packet)[0]][1])
    header_structure_match = re.findall(HEADER_PATTERN.encode(), packet)[1:header_num+1]
    headers_dict = {}
    for match in header_structure_match:
        match = match.decode()
        segments = match.split(":")
        header, value = segments[0], ":".join(segments[1:])
        headers_dict[header] = value[:-2]
    return headers_dict


def get_body(packet: bytes) -> bytes:
    header_num = len(CODES[get_packet_code(packet)[0]][1])
    return b"\x1d\x0d".join(packet.split(SEP)[header_num+1:])[:-1]


def parse_packet_bytes(packet: bytes) -> tuple[tuple[str, str], dict[str, str], bytes]:
    if not is_valid_packet_structure(packet):
        raise PacketStructureError("Invalid packet structure")
    code_segments = get_packet_code(packet)
    headers_dict = get_headers_dict(packet)
    body = get_body(packet)
    return code_segments, headers_dict, body


class PacketInfo:
    def __init__(self, packet: bytes):
        # Temporary assignment, only until parsing. Because the functions that parse the packet are unsafe until we
        # verify the packets' structure. After checking the packets' structure we can use the parsing method to assign
        # values to the attributes
        (self.code, self.desc), self.headers, self.body = parse_packet_bytes(packet)
        self.raw_packet = packet
        if not is_consistent_packet(self):
            raise PacketContentsError(f"Packet contents are not consistent with the packets code: {packet}")

    def verify_code(self, expected: str) -> None:
        if self.code != expected:
            raise PacketContentsError(f"Unexpected packet code, expected {expected}, got {self.code}")

    def validate_content_size(self) -> None:
        if len(self.desc.encode(CHARSET)) > MAX_TITLE_SIZE:
            raise PacketContentsError(f"Packet title exceeds max size {MAX_TITLE_SIZE}")

        for key, field in self.headers.items():
            if len(field.encode(CHARSET)) > MAX_FIELD_SIZE:
                raise PacketContentsError(f"Field of header {key} exceeds max size {MAX_FIELD_SIZE}.")

        if len(self.body) > MAX_FILE_SIZE:
            raise PacketContentsError(f"Body of packet {len(self.body)} exceeds max size {MAX_FILE_SIZE}.")

    def __str__(self) -> str:
        """
        Regular __str__ function
        """
        code_line = f"Code header: {self.code}:{self.desc}\n"
        header_lines = [f"Header: {title}:{value}\n" for title, value in self.headers.items()]
        header_line = "".join(header_lines)
        body_line = f"Body: {repr(self.body)}"
        return code_line + header_line + body_line


def is_consistent_packet(packet: PacketInfo) -> bool:
    """
    Verifies that the packets' code, description, and headers all match each other and that all headers are present
    :param packet: the raw packet string
    :return: does the packet's code match its description and headers
    """
    code, desc = packet.code, packet.desc
    headers = packet.headers
    try:
        if CODES[code][0] != desc:
            return False
        for header_name in CODES[code][1]:
            if header_name not in headers.keys():
                return False
        return True
    except KeyError:
        return False
