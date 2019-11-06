import asyncio
import atexit
import logging
from abc import ABCMeta
from asyncio import Task
from contextlib import asynccontextmanager
from datetime import timedelta

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer, JsonWebsocketConsumer
from django.utils import timezone

from .protocol.messages import MessageEncoder, MessageDecoder, PingMessage, PongMessage
from .models import Appliance

# Get an instance of a logger
logger = logging.getLogger(__name__)


class ApplianceConsumer(JsonWebsocketConsumer, metaclass=ABCMeta):
    appliance_uuid: str

    @classmethod
    def encode_json(cls, content):
        return MessageEncoder.encode(content)

    @classmethod
    def decode_json(cls, text_data):
        return MessageDecoder.decode(text_data)

    def __init__(self, scope):
        super().__init__(scope)
        kwargs = scope['url_route']['kwargs']
        self.appliance_uuid = kwargs['appliance_uuid']


    def connect(self):
        logger.info(f"[{self.appliance_uuid}] Connecting...")
        super().connect()
        logger.info(f"[{self.appliance_uuid}] Connected!")
        self.status_up()

    def disconnect(self, code):
        logger.info(f"[{self.appliance_uuid}] Disconnected!")
        super().disconnect(code)
        self.status_down()

    def receive_json(self, msg, **kwargs):
        if isinstance(msg, PingMessage):
            self.receive_ping(msg)

    def receive_ping(self, ping_msg: PingMessage):
        self.send_pong(ping_msg.ping)

    def send_pong(self, content: str):
        pong_msg = PongMessage(pong=content)
        self.send_json(pong_msg)

    # Database Actions
    # ----------------

    def status_up(self):
        appliance = Appliance.objects.get(pk=self.appliance_uuid)
        appliance.status_up()
        appliance.last_connected_at = timezone.now()
        appliance.save()
        logger.info(f"Appliance UP {self.appliance_uuid}")

    def status_unresponsive(self):
        appliance = Appliance.objects.get(pk=self.appliance_uuid)
        appliance.status_up()
        appliance.save()
        logger.info(f"Appliance UNRESPONSIVE {self.appliance_uuid}")

    def status_down(self):
        appliance = Appliance.objects.get(pk=self.appliance_uuid)
        appliance.status_down()
        appliance.save()
        logger.info(f"Appliance DOWN {self.appliance_uuid}")


class DummyConsumer(ApplianceConsumer):

    def connect(self):
        print("CONNECTED!")
        super().connect()
