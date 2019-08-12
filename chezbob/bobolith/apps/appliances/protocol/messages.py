from bidict import bidict
from django.conf import settings


class MessageHeader:
    __slots__ = ['msg_type', 'version']

    msg_type: str
    version: int

    def __init__(self, msg_type, version=None):
        self.msg_type = msg_type
        if version is None:
            self.version = settings.BOBOLITH_PROTOCOL_VERSION


MESSAGE_TYPES = bidict()


def message_mixin(msg_type: str):
    class MessageMixin:
        __slots__ = ['header']

        header: MessageHeader

        def __init__(self, header=None, **kwargs):
            if header is None:
                self.header = MessageHeader(msg_type=msg_type)

            for key, value in kwargs.items():
                setattr(self, key, value)

        def __init_subclass__(cls, **kwargs):
            if cls not in MESSAGE_TYPES.inverse:
                MESSAGE_TYPES[msg_type] = cls

        def to_json(self):
            return {slot: getattr(self, slot)
                    for slot in self.__slots__
                    if hasattr(self, slot)}

    return MessageMixin


class PingMessage(message_mixin('ping')):
    __slots__ = ['ping']

    ping: str


class PongMessage(message_mixin('pong')):
    __slots__ = ['pong']

    pong: str
