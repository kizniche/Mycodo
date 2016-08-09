# -*- coding: utf-8 -*-

from __future__ import print_function # In python 2.7
import sys

import datetime
import time
import io
import os
import threading
import picamera


class CameraStream(object):
    thread = None  # background thread that reads frames from camera
    frame = None  # current frame is stored here by background thread
    last_access = 0  # time of last client access to the camera
    terminate = False

    def initialize(self):
        if CameraStream.thread is None:
            # start background frame thread
            CameraStream.thread = threading.Thread(target=self._thread)
            CameraStream.thread.start()

            # wait until frames start to be available
            while self.frame is None:
                time.sleep(0)

    def is_running(self):
        if CameraStream.thread is None:
            return False
        return True

    def terminate(self):
        CameraStream.terminate = True

    def get_frame(self):
        CameraStream.last_access = time.time()
        self.initialize()
        return self.frame

    @classmethod
    def _thread(cls):
        try:
            with picamera.PiCamera() as camera:
                # camera setup
                camera.resolution = (1024, 768)
                camera.hflip = True
                camera.vflip = True

                # let camera warm up
                camera.start_preview()
                time.sleep(2)

                stream = io.BytesIO()
                for x in camera.capture_continuous(stream, 'jpeg',
                                                     use_video_port=True):
                    # store frame
                    stream.seek(0)
                    cls.frame = stream.read()

                    # reset stream for next frame
                    stream.seek(0)
                    stream.truncate()

                    # if there hasn't been any clients asking for frames in
                    # the last 10 seconds stop the thread
                    if time.time() - cls.last_access > 10 or cls.terminate:
                        break
        except:
            pass
        cls.thread = None



class CameraTimelapse(object):
    thread = None
    interval_sec = None
    run_time_sec = None
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    timelapse_path = os.path.dirname(os.path.realpath(__file__))+'/../../camera-timelapse/'
    if not os.path.exists(timelapse_path):
        os.makedirs(timelapse_path)
    timelapse_file = timestamp+'-img-{counter:03d}.jpg'
    timelapse_pathfile = timelapse_path+timelapse_file

    def initialize(self):
        if CameraTimelapse.thread is None:
            CameraTimelapse.thread = threading.Thread(target=self._thread)
            CameraTimelapse.thread.start()

    def is_running(self):
        if CameraTimelapse.thread is None:
            return False
        return True

    def terminate(self):
        CameraTimelapse.terminate = True

    def start_timelapse(self, interval_sec, run_time_sec):
        CameraTimelapse.terminate = False
        CameraTimelapse.interval_sec = float(interval_sec)
        CameraTimelapse.run_time_sec = time.time()+float(run_time_sec)
        self.initialize()

    @classmethod
    def _thread(cls):
        try:
            with picamera.PiCamera() as camera:
                camera.resolution = (1296, 972)
                camera.hflip = True
                camera.vflip = True
                camera.start_preview()
                time.sleep(2)
                for filename in camera.capture_continuous(cls.timelapse_pathfile):
                    if time.time() > cls.run_time_sec or cls.terminate:
                        break
                    time.sleep(cls.interval_sec)
        except Exception as msg:
            print('Timelapse Error: {}'.format(msg), file=sys.stderr)
        cls.thread = None
