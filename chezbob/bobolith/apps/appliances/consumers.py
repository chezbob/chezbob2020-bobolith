import asyncio
from abc import ABCMeta
from asyncio import Task
from datetime import timedelta

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from dacite import from_dict
from django.utils.datetime_safe import datetime

from chezbob.bobolith.apps.appliances.protocol import messages as msgs
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
        header = from_dict(data_class=msgs.MessageHeader, data=content)
        klass = msgs.msg_types[header.msg_type]
        msg = from_dict(data_class=klass, data=content)

        return await self.receive_message(msg, **kwargs)

    async def receive_message(self, msg, **kwargs):
        print(f"RECEIVED MESSAGE: {msg}")
        pass

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

    async def _check_heartbeat(self):
        timeout = ApplianceConsumer.HEARTBEAT_TIMEOUT
        heartbeat_delta = timedelta(seconds=timeout)

        while True:
            print("WAITING FOR TIMEOUT...")
            await asyncio.sleep(timeout)
            print("TIMED OUT...")

            last_heartbeat = await self._get_last_heartbeat()
            print(f"LAST HEARTBEAT: {last_heartbeat}")

            if not last_heartbeat:
                print("NO LAST HEARTBEAT")
                await self.status_unresponsive()
                continue

            now = datetime.now()

            if last_heartbeat + heartbeat_delta < now:
                print("DIDN'T RECEIVE HEARTBEAT")
                await self.status_unresponsive()


class DummyConsumer(ApplianceConsumer):

    async def connect(self):
        print("CONNECTED!")
        await super().connect()
