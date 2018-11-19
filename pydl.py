#!/usr/local/bin/python3.7
import asyncio
from music import MusicCore


async def main():
    c = MusicCore()
    await c.queue(sys.argv[1:])
    await c.process_queue()

if __name__ == "__main__":
    import sys
    if (sys.argv is None) or (len(sys.argv) <= 1):
        print("Can't load program without at least one (1) URL")
        exit()
    asyncio.run(main())
else:
    print("This script is a program, not a module")

