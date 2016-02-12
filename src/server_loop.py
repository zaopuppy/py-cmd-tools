#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import time
import asyncio


# import contextlib
# @contextlib.contextmanager
# def lock_condition(cond: threading.Condition):
#     cond.acquire()
#     yield
#     cond.release()


# class Future(object):
#     def __init__(self):
#         self._condition = threading.Condition
#         self._result = None
#         self._canceled = False
#
#     def cancel(self):
#         self._canceled = True
#         self._condition.notify()
#
#     def wait(self, timeout=-1):
#         with lock_condition(self._condition):
#             self._condition.wait(timeout=timeout)
#
#     def set_result(self, result):
#         self._result = result
#
#     def get(self):
#         return self._result
#
#     def add_listener(self, listener):
#         pass


class SocketServer(object):
    def __init__(self, event_loop, port=0):
        self._event_loop = event_loop
        self._port = port
        self._started = False

    def listen(self, port: int):
        self._port = port

    def run(self):
        pass
        # with lock_condition(cond):
        #     print('begin to run')
        #     time.sleep(3)
        #     cond.notify()
        #     print('end running')

    def check_start(self):
        if self._started:
            raise Exception('already started')
        self._started = True

    def start(self):
        self.check_start()

        cond = threading.Condition()

        thread = threading.Thread(target=self.run, args=(cond,))
        thread.start()

        return cond

    def stop(self):
        pass


if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    server = SocketServer(loop)
    server.listen(1983)
    f = server.start()
    f.wait()

    asyncio.get_event_loop().run_forever()
