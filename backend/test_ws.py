import asyncio
import websockets

async def main():
    async with websockets.connect("ws://127.0.0.1:8000/api/v1/ws") as ws:
        for _ in range(3):
            print(await ws.recv())

asyncio.run(main())