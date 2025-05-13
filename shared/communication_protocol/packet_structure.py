# WHEN CHANGING SEPERATOR AND END - ALSO CHANGE REGEX ACCORDINGLY
SEP = b"\x1d\x0d"  # protocol seperator: group seperator + carriage return
END = b"\x04"  # end of packet marker

MAX_TITLE_SIZE = 128  # 128B aka 128 characters
MAX_FIELD_SIZE = 128  # 128B aka 128 characters
MAX_FILE_SIZE = int(1.6e7)  # 16MB


"""
"CODE": ("DESCRIPTION",
        [
            "header1name",
            "header2name",
        ]),
    "000": ("", 
            []),
"""
CODES: dict[str, tuple[str, list[str]]] = {
    # 0xx: Informational, file uploads
    "000": ("File upload",
            []),

    # 1xx: Client requests and related (only client sends)
    "100": ("BPCS steganography encoding request",  # vessel image in body, followed by message upload
            [
                "encryption-key",
                "ecc-block-size",
                "ecc-symbol-num",
                "alpha",
            ]),
    "101": ("LSB steganography encoding request",  # vessel image in body, followed by message upload
            [
                "encryption-key",
                "ecc-block-size",
                "ecc-symbol-num",
                "number-of-sacrificed-bits"
            ]),

    "120": ("Steganography decoding request",  # vessel image in body, followed by token upload
            []),

    "140": ("BPCS maximum capacity calculation request",  # image in body
            [
                "ecc-block-size",
                "ecc-symbol-num",
                "alpha",
            ]),
    "141": ("LSB maximum capacity calculation request",  # image in body
            [
                "ecc-block-size",
                "ecc-symbol-num",
                "number-of-sacrificed-bits",
            ]),

    "160": ("Bitplane slicing request",  # image in body
            []),
    "161": ("Image difference calculation request",
            [
                "show-exact-diff",
            ]),

    # 2xx: Server replies, updates and related (only server sends)
    "200": ("Accepted request",
            []),
    "201": ("Status update",
            [
                "status"
            ]),
    "202": ("Encoding products",  # stegged in body, followed by token upload
            []),
    "203": ("Decoding products",  # data in body
            []),
    "204": ("Capacity calculation products",
            [
                "max-bytes-capacity",
            ]),
    "260": ("Bitplane slicing products image sequence",  # image in body
            [
                "image-name",
            ]),
    "261": ("Image difference calculation products",   # diff image in body
            [
                "red-diff",
                "green-diff",
                "blue-diff",
            ]),
    # 3xx: Client-specific connection termination messages (client sends to server)

    # 4xx: Server-specific connection termination messages (server sends to client)
    "400": ("Internal server error",
            []),
    "401": ("Steganography error",
            [
                "description",
            ]),
    "402": ("Content wrapper error",
            [
                "description",
            ]),
    "403": ("There is an existing client from this address and port",
            []),

    # 5xx: Protocol and non-side specific errors (allways followed by disconnecting)
    "500": ("Disconnect notification",
            [
                "reason",
            ]),
    "501": ("Transmission protocol error",
            []),
    "502": ("Packet structure error",
            []),
    "503": ("Packet contents error",
            [
                "description",
            ]),
}
