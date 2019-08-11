import asyncio
from abc import ABCMeta
from asyncio import Task
from dataclasses import asdict
from datetime import timedelta

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from dacite import from_dict
from django.conf import settings
from django.utils.datetime_safe import datetime

from chezbob.bobolith.apps.appliances.protocol import *
from .models import Appliance


class ApplianceConsumer(AsyncJsonWebsocketConsumer, metaclass=ABCMeta):
    HEARTBEAT_TIMEOUT = 10  # in seconds

    appliance: Appliance
    heartbeat_task: Task

    def __init__(self, scope, appliance):
        super().__init__(scope)
        self.appliance = appliance
        self.heartbeat_task = asyncio.create_task(self._check_heartbeat())

    async def connect(self):
        await super().connect()
        await self.status_up()

    async def disconnect(self, code):
        await super().disconnect(code)
        self.heartbeat_task.cancel()
        await self.status_down()

    async def receive_json(self, content, **kwargs):
        # todo: handle bad parse gracefully
        header = from_dict(data_class=MessageHeader, data=content)
        klass = msg_types[header.msg_type]
        msg = from_dict(data_class=klass, data=content)

        return await self.receive_message(msg, **kwargs)

    async def receive_message(self, msg, **kwargs):
        if isinstance(msg, PingMessage):
            await self.receive_ping(msg)

    async def receive_ping(self, ping_msg: PingMessage):
        print(f"RECEIVED {ping_msg}")
        await self._set_last_heartbeat()
        await self.send_pong(ping_msg.ping)

    async def send_pong(self, content: str):
        pong_msg = PongMessage(
            version=settings.BOBOLITH_PROTOCOL_VERSION,
            msg_type=msg_types.inverse[PongMessage],
            pong=content
        )
        await self.send_json(asdict(pong_msg))

    @database_sync_to_async
    def status_up(self):
        print("UP!")
        self.appliance.status = Appliance.STATUS_UP
        self.appliance.last_connected_at = datetime.now()
        self.appliance.save()

    @database_sync_to_async
    def status_down(self):
        print("DOWN!")
        self.appliance.status = Appliance.STATUS_DOWN
        self.appliance.save()

    @database_sync_to_async
    def status_unresponsive(self):
        print("UNRESPONSIVE!")
        self.appliance.status = Appliance.STATUS_UNRESPONSIVE
        self.appliance.save()

    @database_sync_to_async
    def _get_last_heartbeat(self):
        return self.appliance.last_heartbeat_at

    @database_sync_to_async
    def _set_last_heartbeat(self):
        self.appliance.last_heartbeat_at = datetime.now()
        self.appliance.status = Appliance.STATUS_UP
        self.appliance.save()

    async def _check_heartbeat(self):
        timeout = ApplianceConsumer.HEARTBEAT_TIMEOUT
        heartbeat_delta = timedelta(seconds=timeout)

        while True:
            await asyncio.sleep(timeout)

            last_heartbeat = await self._get_last_heartbeat()

            if not last_heartbeat:
                await self.status_unresponsive()
                continue

            now = datetime.now()

            if last_heartbeat + heartbeat_delta < now:
                await self.status_unresponsive()


class DummyConsumer(ApplianceConsumer):

    async def connect(self):
        print("CONNECTED!")
        await super().connect()
