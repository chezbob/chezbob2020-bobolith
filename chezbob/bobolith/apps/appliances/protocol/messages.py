from dataclasses import dataclass

from bidict import frozenbidict
from django.conf import settings


@dataclass(frozen=True)
class MessageHeader:
    version: int
    msg_type: str

    def __post_init__(self):
        assert self.version == settings.BOBOLITH_PROTOCOL_VERSION
        assert self.msg_type is not None

        if self.__class__ is not MessageHeader:
            assert self.msg_type == msg_types.inverse[self.__class__]


@dataclass(frozen=True)
class PingMessage(MessageHeader):
    ping: str

    def __post_init__(self):
        super().__post_init__()


@dataclass(frozen=True)
class PongMessage(MessageHeader):
    pong: str

    def __post_init__(self):
        super().__post_init__()


msg_types = frozenbidict({
    'ping': PingMessage,
    'pong': PongMessage
})
