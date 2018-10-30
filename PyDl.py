#!/usr/local/bin/python3.7
import asyncio
from music import MusicCore

c = MusicCore()
loop = asyncio.get_event_loop()
loop.run_until_complete(c.queue(["https://www.youtube.com/watch?v=mkl1qRw3F8g"]))
