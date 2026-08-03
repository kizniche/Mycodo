# coding=utf-8
import asyncio
import functools
import threading

import logging

_LOG = logging.getLogger(__name__)

class Future:
    """A simple future-like object that can be used to wait for an async
    function to complete in a synchronous way."""
    def __init__(self):
        self.event = threading.Event()
        self.retval = None
        self.exception = None

    def set_result(self, retval=None):
        self.retval = retval
        self.event.set()

    def set_exception(self, exception):
        self.exception = exception
        self.event.set()

    def wait(self, timeout=None):
        self.event.wait(timeout)
        if self.exception:
            # Re-raise the exception in the main thread
            raise self.exception
        return self.retval

class AsyncLoop:
    """A class that runs an asyncio event loop in a separate thread, and
    provides a way to call async functions from the main thread."""
    def __init__(self):
        self._loop = None
        self._stop_event = asyncio.Event()
        self._thread = None

    def call_async(self, func):
        async def wrapper(future: Future):
            try:
                future.set_result(await func)
            except Exception as e:
                _LOG.error(f"Caught exception: {e}")
                future.set_exception(e)

        future = Future()
        self._loop.call_soon_threadsafe(
            functools.partial(self._loop.create_task, wrapper(future))
        )
        return future.wait()

    def initialize(self):
        start_event = threading.Event()
        self._thread = threading.Thread(
            target=asyncio.run, args=(self._main(start_event),)
        )
        self._thread.start()
        # Wait for the thread to start
        start_event.wait()

    def stop(self):
        if self._thread:
            self._loop.call_soon_threadsafe(self._stop_event.set)
            self._thread.join()
            self._thread = None

    async def _main(self, start_event: threading.Event):
        self._loop = asyncio.get_running_loop()

        start_event.set()  # Signal that the thread has started
        # Loop started, process events until stop is requested
        await self._stop_event.wait()
