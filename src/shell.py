#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A simple enhanced system shell wrapper

By Yi Zhao 2/25/2015
"""

import asyncio
import functools
import sys
import os
import os.path
import subprocess
import time


def log(msg):
    print(msg)


class SocketReader(object):
    def __init__(self, fd: int, loop=None):
        self._fd = fd
        self._loop = loop or asyncio.get_event_loop()

    async def read(self, n=1):
        self._loop.add_reader(self._fd, self._on_read)

    def _on_read(self):
        self._loop.sock_recv()


def async_input(promise: asyncio.Future, loop: asyncio.AbstractEventLoop):
    pass


class Shell(asyncio.Protocol):
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self._prompt = '> '
        self._loop = loop
        self._cmd = 'C:/Windows/SysWOW64/cmd.exe'

    def start(self):
        self._loop.create_task(self._start())

    async def _start(self):
        in_r, in_w = os.pipe()
        out_r, out_w = os.pipe()
        err_r, err_w = os.pipe()

        process = None
        try:
            process = await asyncio.create_subprocess_exec(
                self._cmd,
                stdin=os.fdopen(in_r, 'rb'),
                stdout=os.fdopen(out_w, 'wb'),
                stderr=os.fdopen(err_w, 'wb'))

            in_trans, _ = await self._loop.connect_write_pipe(self, os.fdopen(in_w, 'wb'))
            await self._loop.connect_read_pipe(self, os.fdopen(out_r, 'rb'))
            await self._loop.connect_read_pipe(self, os.fdopen(err_r, 'rb'))

            while True:
                data = await async_input(self._loop)
                if not data:
                    break
                in_trans.write(data)

        finally:
            # clean up
            os.close(in_w)
            os.close(out_r)
            os.close(err_r)
            if process is not None:
                process.close()

    def connection_lost(self, exc):
        super().connection_lost(exc)

    def connection_made(self, transport):
        super().connection_made(transport)

    def pause_writing(self):
        super().pause_writing()

    def resume_writing(self):
        super().resume_writing()

    def data_received(self, data):
        super().data_received(data)

    def eof_received(self):
        super().eof_received()


def setup_loop():
    if sys.platform == 'win32':
        asyncio.set_event_loop(asyncio.ProactorEventLoop())
    return asyncio.get_event_loop()


def main():
    loop = setup_loop()

    shell = Shell(loop)
    shell.start()

    loop.run_forever()


def foo(fd):
    data = os.read(5)
    print(data)


import threading


def run_handler(stdin, stdout, stderr):
    log('run handler: {}, {}, {}'.format(stdin, stdout, stderr))
    process = subprocess.Popen([sys.executable, '-i'], stdin=stdin, stdout=stdout, stderr=stderr)
    # process = subprocess.Popen(['C:/Windows/SysWOW64/cmd.exe'], stdin=stdin, stdout=stdout, stderr=stderr)
    log('subprocess created, waiting')
    process.communicate()


def run_reader(fd):
    log('fd: {}'.format(fd))
    with os.fdopen(fd, 'rb') as fp:
        for line in iter(functools.partial(fp.read1, 2048), b''):
            # IncrementalDecoder is needed
            print(line.decode('utf-8'), end='')


def test_pipe():
    in_r, in_w = os.pipe()
    out_r, out_w = os.pipe()
    # err_r, err_w = os.pipe()
    sub_thread = threading.Thread(target=run_handler, args=(in_r, out_w, subprocess.STDOUT))
    sub_thread.start()
    out_thread = threading.Thread(target=run_reader, args=(out_r,))
    out_thread.start()
    # err_thread = threading.Thread(target=run_reader, args=(err_r,))
    # err_thread.start()
    with os.fdopen(in_w, 'wb') as fp:
        while True:
            s = input('') + '\n'
            fp.write(s.encode('utf-8'))
            fp.flush()


if __name__ == "__main__":
    test_pipe()
    # type of sys.stdin: io.TextIOWrapper
    # loop = asyncio.get_event_loop()
    # loop.add_reader(0, functools.partial(foo, 0))
    # loop.run_forever()

