class ConnectionStreamError(Exception):
    pass


class TransmissionProtocolError(ConnectionStreamError):
    """
    Will be raised if a received packet does not follow the transmission protocol.
    """
    pass


class PacketStructureError(ConnectionStreamError):
    """
    Will be raised if a received packet has incorrect structure, or if its contents are inconsistent.
    """
    pass


class PacketContentsError(ConnectionStreamError):
    """
    Will be raised if:
    1. Packets contents are inconsistent with each other
    2. Expected a packet of different code
    3. Expected packet contents to be of a certain type / structure
    4. Packet contains header fields or body that exceed the maximum size
    """
    pass
