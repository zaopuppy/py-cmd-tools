#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import time


def log(msg):
    print(msg)


async def foo():
    return 5


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    coro = foo()
    # v = loop.run_until_complete(coro)
    f = asyncio.ensure_future(coro)
    log(id(f))
    # f.add_done_callback(lambda v: print(id(v)))
    loop.run_forever()
    # time.sleep(1)
    # log(f.result())


