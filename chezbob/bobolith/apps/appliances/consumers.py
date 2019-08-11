from abc import ABCMeta

from channels.generic.websocket import AsyncJsonWebsocketConsumer


class ApplianceConsumer(AsyncJsonWebsocketConsumer, metaclass=ABCMeta):
    pass


class DummyConsumer(ApplianceConsumer):
    async def connect(self):
        print("CONNECTED!")
        await super().connect()

    async def receive_json(self, content, **kwargs):
        print(f"RECEIVED JSON: {content}")
