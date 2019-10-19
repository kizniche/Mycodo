# -*- coding: utf-8 -*-
# From https://github.com/miguelgrinberg/flask-video-streaming
import threading
import time

try:
    from greenlet import getcurrent as get_ident
except ImportError:
    try:
        from thread import get_ident
    except ImportError:
        from _thread import get_ident


class CameraEvent(object):
    """An Event-like class that signals all active clients when a new frame is
    available.
    """
    def __init__(self):
        self.events = {}

    def wait(self):
        """Invoked from each client's thread to wait for the next frame."""
        ident = get_ident()
        if ident not in self.events:
            # this is a new client
            # add an entry for it in the self.events dict
            # each entry has two elements, a threading.Event() and a timestamp
            self.events[ident] = [threading.Event(), time.time()]
        return self.events[ident][0].wait()

    def set(self):
        """Invoked by the camera thread when a new frame is available."""
        now = time.time()
        remove = None
        for ident, event in self.events.items():
            if not event[0].isSet():
                # if this client's event is not set, then set it
                # also update the last set timestamp to now
                event[0].set()
                event[1] = now
            else:
                # if the client's event is already set, it means the client
                # did not process a previous frame
                # if the event stays set for more than 5 seconds, then assume
                # the client is gone and remove it
                if now - event[1] > 5:
                    remove = ident
        if remove:
            del self.events[remove]

    def clear(self):
        """Invoked from each client's thread after a frame was processed."""
        self.events[get_ident()][0].clear()


class BaseCamera(object):
    thread = {}  # background thread that reads frames from camera
    frame = {}  # current frame is stored here by background thread
    last_access = {}  # time of last client access to the camera
    event = {}
    running = {}

    def __init__(self, unique_id=None):
        """Start the background camera thread if it isn't running yet."""
        self.unique_id = unique_id
        BaseCamera.event[self.unique_id] = CameraEvent()
        BaseCamera.running[self.unique_id] = True

        if self.unique_id not in BaseCamera.thread:
            BaseCamera.thread[self.unique_id] = None

        if BaseCamera.thread[self.unique_id] is None:
            BaseCamera.last_access[self.unique_id] = time.time()

            # start background frame thread
            BaseCamera.thread[self.unique_id] = threading.Thread(
                target=self._thread, args=(self.unique_id,))
            BaseCamera.thread[self.unique_id].start()

            # wait until frames are available
            while self.get_frame() is None:
                time.sleep(0)

    def get_frame(self):
        """Return the current camera frame."""
        BaseCamera.last_access[self.unique_id] = time.time()

        # wait for a signal from the camera thread
        BaseCamera.event[self.unique_id].wait()
        BaseCamera.event[self.unique_id].clear()

        return BaseCamera.frame[self.unique_id]

    @staticmethod
    def frames():
        """"Generator that returns frames from the camera."""
        raise RuntimeError('Must be implemented by subclasses')

    @classmethod
    def _thread(cls, unique_id):
        """Camera background thread."""
        print('[{id}] Starting camera thread'.format(id=unique_id))
        frames_iterator = cls.frames()
        for frame in frames_iterator:
            BaseCamera.frame[unique_id] = frame
            BaseCamera.event[unique_id].set()  # send signal to clients
            time.sleep(0)

            # if there haven't been any clients asking for frames in
            # the last 10 seconds then stop the thread
            if time.time() - BaseCamera.last_access[unique_id] > 10:
                frames_iterator.close()
                print('[{id}] Stopping camera thread due to '
                      'inactivity'.format(id=unique_id))
                break
            if not BaseCamera.running[unique_id]:
                frames_iterator.close()
                print('[{id}] Camera thread instructed to '
                      'shut down'.format(id=unique_id))
                break
        BaseCamera.thread[unique_id] = None
        BaseCamera.running[unique_id] = False

    @staticmethod
    def stop(unique_id):
        BaseCamera.running[unique_id] = False

    @staticmethod
    def is_running(unique_id):
        return BaseCamera.running[unique_id]
