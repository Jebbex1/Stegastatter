# WHEN CHANGING SEPERATOR AND END - ALSO CHANGE REGEX ACCORDINGLY
SEP = b"\x1d\x0d"  # protocol seperator: group seperator + carriage return
END = b"\x04"  # end of packet marker

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
    "000": ("Image upload",
            []),


    # 1xx: Client requests and related (only client sends)
    "100": ("BPCS steganography encoding request",  # followed by image upload
            [
                "encryption-key",
                "ecc-block-size",
                "ecc-symbol-num",
                "alpha",
            ]),
    "101": ("BPCS steganography decoding request",  # token in body, followed by image upload
            []),

    # 2xx: Server replies, updates and related (only server sends)
    "200": ("Got request",
            []),
    "201": ("Status update",
            [
                "status"
            ]),
    "202": ("Encoding products",  # token in body, followed by image upload
            []),
    "203": ("Decoding products",  # data in body
            []),

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


    # 5xx: Protocol and non-side specific errors (allways followed by disconnecting)
    "500": ("Normal disconnect",
            [
                "reason",
            ]),
    "501": ("Transmission protocol error",
            []),
    "502": ("Packet structure error",
            []),
    "503": ("",
            []),
}
