import asyncio
import logging
from abc import ABCMeta
from asyncio import Task
from dataclasses import asdict
from datetime import timedelta
from typing import Optional

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from dacite import from_dict
from django.conf import settings
from django.utils import timezone

from chezbob.bobolith.apps.appliances.protocol import *
from .models import Appliance

# Get an instance of a logger
logger = logging.getLogger(__name__)


class AsyncApplianceContextManager:
    appliance_uuid: str
    instance: Optional[Appliance]

    def __init__(self, appliance_uuid):
        self.appliance_uuid = appliance_uuid
        self.appliance = None

    @database_sync_to_async
    def get_appliance(self):
        self.appliance = Appliance.objects.get(pk=self.appliance_uuid)
        return self.appliance

    @database_sync_to_async
    def save_appliance(self, appliance: Appliance):
        appliance.save()
        del self.appliance

    async def __aenter__(self):
        return await self.get_appliance()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.save_appliance(self.appliance)


class ApplianceConsumer(AsyncJsonWebsocketConsumer, metaclass=ABCMeta):
    HEARTBEAT_TIMEOUT = 3  # in seconds

    appliance_uuid: str
    heartbeat_task: Task

    def __init__(self, scope, appliance_uuid: str):
        super().__init__(scope)
        self.appliance_uuid = appliance_uuid
        self.heartbeat_task = asyncio.create_task(self._check_heartbeat())

    async def connect(self):
        logger.info("Connecting...")
        await super().connect()
        logger.info("Connected!")
        await self.status_up()

    async def disconnect(self, code):
        logger.info("Disconnected!")
        await super().disconnect(code)
        self.heartbeat_task.cancel()
        await self.status_down()

    async def receive_json(self, content, **kwargs):
        # todo: handle bad parse gracefully
        header = from_dict(data_class=MessageHeader, data=content)
        klass = msg_types[header.msg_type]
        msg = from_dict(data_class=klass, data=content)

        return await self.receive_message(msg, **kwargs)

    async def receive_message(self, msg, **_kwargs):
        if isinstance(msg, PingMessage):
            await self.receive_ping(msg)

    async def receive_ping(self, ping_msg: PingMessage):
        await self.set_last_heartbeat()
        await self.send_pong(ping_msg.ping)

    async def send_pong(self, content: str):
        pong_msg = PongMessage(
            version=settings.BOBOLITH_PROTOCOL_VERSION,
            msg_type=msg_types.inverse[PongMessage],
            pong=content
        )
        await self.send_json(asdict(pong_msg))

    # Database Actions

    def appliance_context(self):
        return AsyncApplianceContextManager(self.appliance_uuid)

    async def status_up(self):
        async with self.appliance_context() as appliance:
            appliance.status = Appliance.STATUS_UP
            appliance.last_connected_at = timezone.now()
        logger.info(f"Status {self.appliance_uuid} => {Appliance.STATUS_UP}")

    async def status_down(self):
        async with self.appliance_context() as appliance:
            appliance.status = Appliance.STATUS_DOWN
        logger.info(f"Status {self.appliance_uuid} => {Appliance.STATUS_DOWN}")

    async def status_unresponsive(self):
        async with self.appliance_context() as appliance:
            appliance.status = Appliance.STATUS_UNRESPONSIVE
        logger.info(f"Status {self.appliance_uuid} => {Appliance.STATUS_UNRESPONSIVE}")

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
                await self.status_unresponsive()
                continue

            now = timezone.now()
            if last_heartbeat + heartbeat_delta < now:
                await self.status_unresponsive()


class DummyConsumer(ApplianceConsumer):

    async def connect(self):
        print("CONNECTED!")
        await super().connect()
