from abc import ABCMeta

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.utils.datetime_safe import datetime

from .models import Appliance


class ApplianceConsumer(AsyncJsonWebsocketConsumer, metaclass=ABCMeta):
    appliance: Appliance

    def __init__(self, scope, appliance):
        super().__init__(scope)
        self.appliance = appliance

    async def connect(self):
        await super().connect()
        await self.status_up()

    async def disconnect(self, code):
        await super().disconnect(code)
        await self.status_down()

    @database_sync_to_async
    def status_up(self):
        self.appliance.status = Appliance.STATUS_UP
        self.appliance.last_connected_at = datetime.now()
        self.appliance.save()

    @database_sync_to_async
    def status_down(self):
        self.appliance.status = Appliance.STATUS_DOWN
        self.appliance.save()


class DummyConsumer(ApplianceConsumer):

    async def connect(self):
        print("CONNECTED!")
        await super().connect()

    async def receive_json(self, content, **kwargs):
        print(f"RECEIVED JSON: {content}")
