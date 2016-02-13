#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import time
import asyncio
import itertools
import os
import threading


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


async def handle_client(reader, writer):
    stdin, stdout, stderr = notty_test()
    while True:
        raw_data = await reader.read(1024)
        log(raw_data)
        if not raw_data:
            log('connection lose')
            break
        data = raw_data.decode('utf-8')
        log('received: [{}]'.format(data))
        os.write(stdin, data)


def start_server():
    asyncio.set_event_loop(asyncio.ProactorEventLoop())

    loop = asyncio.get_event_loop()

    server_coro = asyncio.start_server(handle_client, '0.0.0.0', 1983)
    server = loop.run_until_complete(server_coro)

    log('started')
    loop.run_forever()

    server.close()
    loop.run_until_complete(server.wait_closed())
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
    # (server-side, client-side)
    in_r, in_w = os.pipe()
    out_r, out_w = os.pipe()
    err_r, err_w = os.pipe()

    process = asyncio.create_subprocess_exec(
        'C:/Windows/SysWOW64/cmd.exe', stdin=in_r, stdout=out_w, stderr=err_w)
    # child_thread = threading.Thread(target=do_child, args=(in_r, out_w, err_w))
    # child_thread.start()
    # server_thread = threading.Thread(target=server_loop, args=(in_w, out_r, err_r))
    # server_thread.start()

    asyncio.get_event_loop().conn
    return in_w, out_r, err_r


if __name__ == '__main__':
    start_server()
    # tty_test()

# END
