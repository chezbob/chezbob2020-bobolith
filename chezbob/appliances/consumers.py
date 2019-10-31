import asyncio
import atexit
import logging
from abc import ABCMeta
from asyncio import Task
from contextlib import asynccontextmanager
from datetime import timedelta

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.utils import timezone

from .protocol.messages import MESSAGE_TYPES, MessageHeader, PingMessage, PongMessage
from .models import Appliance

# Get an instance of a logger
logger = logging.getLogger(__name__)


@atexit.register
def test():
    print("HELLO WORLD!")


class ApplianceConsumer(AsyncJsonWebsocketConsumer, metaclass=ABCMeta):
    HEARTBEAT_TIMEOUT = 10  # in seconds

    appliance_uuid: str
    heartbeat_task: Task

    def __init__(self, scope):
        super().__init__(scope)
        kwargs = scope['url_route']['kwargs']
        self.appliance_uuid = kwargs['appliance_uuid']
        self.heartbeat_task = asyncio.create_task(self._check_heartbeat())

    async def connect(self):
        logger.info(f"[{self.appliance_uuid}] Connecting...")
        await super().connect()
        logger.info(f"[{self.appliance_uuid}] Connected!")
        await self.status_up()

    async def disconnect(self, code):
        logger.info(f"[{self.appliance_uuid}] Disconnected!")
        await super().disconnect(code)
        self.heartbeat_task.cancel()
        await self.status_down()

    async def receive_json(self, content, **kwargs):
        header_content = content.pop('header')
        header = MessageHeader(**header_content)

        klass = MESSAGE_TYPES[header.msg_type]
        msg = klass(header=header, **content)

        return await self.receive_message(msg, **kwargs)

    async def receive_message(self, msg, **_kwargs):
        if isinstance(msg, PingMessage):
            await self.receive_ping(msg)

    async def receive_ping(self, ping_msg: PingMessage):
        await self.set_last_heartbeat()
        await self.send_pong(ping_msg.ping)

    async def send_pong(self, content: str):
        pong_msg = PongMessage(pong=content)
        await self.send_json(pong_msg.to_json())

    # Database Actions
    # ----------------

    @asynccontextmanager
    async def appliance_context(self, save=False):
        appliance = await database_sync_to_async(Appliance.objects.get)(pk=self.appliance_uuid)

        try:
            yield appliance
        finally:
            if save:
                await database_sync_to_async(appliance.save)()

    async def status_up(self):
        async with self.appliance_context(save=True) as appliance:
            appliance.status = Appliance.STATUS_UP
            appliance.last_connected_at = timezone.now()
        logger.info(f"Appliance UP {self.appliance_uuid}")

    async def status_unresponsive(self):
        async with self.appliance_context(save=True) as appliance:
            appliance.status = Appliance.STATUS_UNRESPONSIVE
        logger.info(f"Appliance UNRESPONSIVE {self.appliance_uuid}")

    async def status_down(self):
        async with self.appliance_context(save=True) as appliance:
            appliance.status = Appliance.STATUS_DOWN
        logger.info(f"Appliance DOWN {self.appliance_uuid}")

    # Heartbeat management
    # --------------------

    async def get_last_heartbeat(self):
        async with self.appliance_context() as appliance:
            return appliance.last_heartbeat_at

    async def set_last_heartbeat(self, time=None):
        if time is None:
            time = timezone.now()

        async with self.appliance_context() as appliance:
            appliance.last_heartbeat_at = time
            appliance.status = Appliance.STATUS_UP

    async def _check_heartbeat(self):
        timeout = ApplianceConsumer.HEARTBEAT_TIMEOUT
        heartbeat_delta = timedelta(seconds=timeout)

        while True:
            await asyncio.sleep(timeout)

            last_heartbeat = await self.get_last_heartbeat()

            if not last_heartbeat:
                await self._heartbeat_timed_out()
                continue

            now = timezone.now()
            if last_heartbeat + heartbeat_delta < now:
                await self._heartbeat_timed_out()

    async def _heartbeat_timed_out(self):
        logger.info("Heartbeat timed out.")
        async with self.appliance_context() as appliance:
            if appliance.status == Appliance.STATUS_UP:
                await self.status_unresponsive()
            elif appliance.status == Appliance.STATUS_UNRESPONSIVE:
                await self.close()


class DummyConsumer(ApplianceConsumer):

    async def connect(self):
        print("CONNECTED!")
        await super().connect()
