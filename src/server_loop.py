#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
import time
import asyncio
import itertools
import os
import functools


# if (*amaster = open(ptbuf, O_RDWR | O_NOCTTY)) == -1) {
# 	/* Try SCO style naming */
# 	snprintf(ptbuf, sizeof(ptbuf), "/dev/ptyp%d", i);
# 	snprintf(ttbuf, sizeof(ttbuf), "/dev/ttyp%d", i);
# 	if ((*amaster = open(ptbuf, O_RDWR | O_NOCTTY)) == -1)
# 		continue;
# }
# /* Open the slave side. */
# if ((*aslave = open(ttbuf, O_RDWR | O_NOCTTY)) == -1) {
# 	close(*amaster);
# 	return (-1);
# }
# /* set tty modes to a sane state for broken clients */
# if (tcgetattr(*amaster, &tio) != -1) {
# 	tio.c_lflag |= (ECHO | ISIG | ICANON);
# 	tio.c_oflag |= (OPOST | ONLCR);
# 	tio.c_iflag |= ICRNL;
# 	tcsetattr(*amaster, TCSANOW, &tio);
# }


# pty -> parent
#     close(ttyfd);
# tty -> child
#     close(ptyfd);
#     dup2(ttyfd, 0);
#     dup2(ttyfd, 1);
#     dup2(ttyfd, 2);
#
# server_loop(pid,       ptyfd,        fdout(ptyfd),         -1);
# server_loop(pid_t pid, int fdin_arg, int fdout_arg, int fderr_arg)

def log(msg):
    print(msg)


class PipeReader(asyncio.Protocol):
    def __init__(self, writer):
        self._writer = writer

    def data_received(self, data):
        # log(data.decode('utf-8'))
        self._writer.write(data)

    def eof_received(self):
        log('eof pipe')
        self._writer.write('eof'.encode('utf-8'))


class PipeWriter(asyncio.BaseProtocol):
    def connection_lost(self, exc):
        log('connection lost')

    def connection_made(self, transport):
        log('connection made')

    def pause_writing(self):
        log('pause writing')

    def resume_writing(self):
        log('resume writing')


def create_pipe_reader(writer):
    return PipeReader(writer)


async def handle_client(reader, writer):
    log('new connection')

    loop = asyncio.get_event_loop()

    # do some authenticate work

    in_r, in_w = os.pipe()
    out_r, out_w = os.pipe()
    err_r, err_w = os.pipe()

    process = await asyncio.create_subprocess_exec(
        sys.executable, '-i',
        stdin=os.fdopen(in_r, 'rb'),
        stdout=os.fdopen(out_w, 'wb'),
        stderr=os.fdopen(err_w, 'wb'))

    in_transport, _ = await loop.connect_write_pipe(PipeWriter, os.fdopen(in_w, 'wb'))
    await loop.connect_read_pipe(functools.partial(PipeReader, writer), os.fdopen(out_r, 'rb'))
    await loop.connect_read_pipe(functools.partial(PipeReader, writer), os.fdopen(err_r, 'rb'))

    asyncio.ensure_future(process.communicate(), loop=loop)

    log('read client')
    while True:
        raw_data = await reader.read(1024)
        # log(raw_data)
        if not raw_data:
            log('connection lose')
            break
        # data = raw_data.decode('utf-8')
        # log(data)
        in_transport.write(raw_data)


def start_server():
    if sys.platform in ('win32', 'cygwin'):
        asyncio.set_event_loop(asyncio.ProactorEventLoop())

    loop = asyncio.get_event_loop()

    # start server
    server_coro = asyncio.start_server(handle_client, '0.0.0.0', 1983, loop=loop)
    server = loop.run_until_complete(asyncio.ensure_future(server_coro, loop=loop))

    log('Serving on {}'.format(s.getsockname() for s in server.sockets))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    server.close()
    # loop.run_until_complete(server_future)
    loop.close()


def tty_test():
    major = 'pqrstuvwxyzabcdefghijklmnoABCDEFGHIJKLMNOPQRSTUVWXYZ'
    minor = '0123456789abcdef'
    pty_fd, tty_fd = -1, -1
    for suffix in itertools.product(major, minor):
        pass
        # pty_fd = os.open('/dev/pty' + suffix, os.O_RDWR|os.O_NOCTTY)


def do_child(stdin, stdout, stderr):
    pass


def server_loop(stdin, stdout, stderr):
    pass


def notty_test():
    loop = asyncio.get_event_loop()
    future = asyncio.create_subprocess_shell('/bin/ls')
    # returned a generator
    future = asyncio.create_subprocess_shell('/bin/ls')
    log(future.result())
    process = loop.run_until_complete(future)
    log(str(process.returncode))


def test_pipe():
    in_r, in_w = os.pipe()
    out_r, out_w = os.pipe()

    loop = asyncio.get_event_loop()
    process = loop.run_until_complete(
        asyncio.create_subprocess_exec(
            sys.executable, '-i',
            stdin=os.fdopen(in_r, 'rb'), stderr=os.fdopen(out_w, 'wb'), loop=loop))

    log('register pipe')
    read_transport, _ = loop.run_until_complete(loop.connect_read_pipe(PipeReader, os.fdopen(out_r, 'rb')))
    write_transport, _ = loop.run_until_complete(loop.connect_write_pipe(PipeReader, os.fdopen(in_w, 'wb')))

    asyncio.ensure_future(process.communicate(), loop=loop)

    time.sleep(3)

    write_transport.abort()

    process.terminate()

    loop.run_forever()

if __name__ == '__main__':
    # notty_test()
    start_server()
    # tty_test()
    # test_pipe()

# END
