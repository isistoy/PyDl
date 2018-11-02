#!/usr/local/bin/python3.7
import asyncio
from music import MusicCore


async def main():
    c = MusicCore()
    await c.queue(["https://www.youtube.com/watch?v=mkl1qRw3F8g"])
    await c.process_queue()

asyncio.run(main())

