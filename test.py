# WS client example

import asyncio
import json

import websockets


async def hello():
    # uri = "ws://localhost:8765"
    uri = "ws://127.0.0.1:8000/ws/765d2c49-5d0a-4f4f-a1b2-0694be5b2e48/"
    async with websockets.connect(uri) as websocket:
        # name = input("What's your name? ")
        await websocket.send(json.dumps({"version": 0, "msg_type": "ping", "ping": "Gautam"}))

        greeting = await websocket.recv()
        print(greeting)


asyncio.get_event_loop().run_until_complete(hello())
