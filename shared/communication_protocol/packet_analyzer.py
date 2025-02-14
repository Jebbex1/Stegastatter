import re

import shared.communication_protocol.packet_structure as structure
from shared.communication_protocol.communication_errors import CommunicationError, PacketStructureError

HEADER_PATTERN = r"([\w-]+:[\x20-\x7E]+\x1D\x0D)"

# a regex that matches any correctly structured packets (does not check packet parameters, only its structure)
PACKET_PATTERN = (
    r"^("  # starts with 
    r"(\d{3}:[\w\x20]+\x1D\x0D)"  # code and description
    fr"{HEADER_PATTERN}*"  # headers (zero or more)
    r")"
    
    r".*"  # body
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


def get_packet_code(packet: bytes) -> tuple[bytes, bytes]:
    """
    Gets the packet code and description from the raw packet string
    :param packet: the raw packet string
    :return: <packet code>,<packet string>
    """
    code_parts = packet.split(structure.SEP)[0].split(b":")
    return code_parts[0], code_parts[1]


def get_headers_dict(packet: bytes) -> dict[bytes, bytes]:
    """
    Gets the headers of the packet, and parses them into a dictionary
    :param packet: the raw packet string
    :return: a dictionary of the packet headers,  dict key -> header name and dict value -> header value
    """
    header_num = len(structure.CODES[get_packet_code(packet)[0].decode()][1])
    header_structure_match = re.findall(HEADER_PATTERN.encode(), packet)[1:header_num+1]
    headers_dict = {}
    for match in header_structure_match:
        segments = match.split(b":")
        header, value = segments[0], b":".join(segments[1:])
        headers_dict[header] = value[:-2]
    return headers_dict


def get_body(packet: bytes) -> bytes:
    header_num = len(structure.CODES[get_packet_code(packet)[0].decode()][1])
    return b"\x1d\x0d".join(packet.split(structure.SEP)[header_num+1:])[:-1]


def parse_packet_bytes(packet: bytes) -> tuple[tuple[bytes, bytes], dict[bytes, bytes], bytes]:
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
            raise PacketStructureError("Packet contents are not consistent")

    def __str__(self) -> str:
        """
        Regular __str__ function
        """
        code_line = f"Code header: {self.code.decode()}:{self.desc.decode()}\n"
        header_lines = [f"Header: {title.decode()}:{value.decode()}\n" for title, value in self.headers.items()]
        header_line = "".join(header_lines)
        body_line = f"Body: {repr(self.body.decode())}"
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
        if structure.CODES[code.decode()][0] != desc.decode():
            return False
        for header_name in structure.CODES[code.decode()][1]:
            if header_name.encode() not in headers.keys():
                return False
        return True
    except KeyError:
        return False
