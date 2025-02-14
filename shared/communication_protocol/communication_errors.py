
class CommunicationError(Exception):
    pass


class TransmissionProtocolError(CommunicationError):
    """
    Will be raised if a received packet does not follow the transmission protocol.
    """
    pass


class PacketStructureError(CommunicationError):
    """
    Will be raised if a received packet has incorrect structure, or if its contents are inconsistent.
    """
    pass
