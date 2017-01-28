# -*- coding: utf-8 -*-
from __future__ import print_function  # In python 2.7
import logging
import datetime
import time
import io
import os
import threading
import picamera

from utils.system_pi import (
    assure_path_exists,
    set_user_grp
)

from config import INSTALL_DIRECTORY

logger = logging.getLogger('mycodo.devices.picamera')


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

    @staticmethod
    def is_running():
        if CameraStream.thread is None:
            return False
        return True

    @staticmethod
    def terminate_controller():
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
                for _ in camera.capture_continuous(stream, 'jpeg',
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
        except Exception as e:
            logger.error("{cls} raised an error during read() call: "
                         "{err}".format(cls=type(cls).__name__, err=e))
        cls.thread = None


#
# Camera record
#

def camera_record(record_type, settings, duration_sec=None,
                  start_time=None, capture_number=None):
    """
    Record still/timelapse images, and video

    :param record_type: 'photo', 'timelapse', or 'video'
    :param settings: picamera settings object
    :param duration_sec: video duration
    :param start_time: timelapse start time (for filename)
    :param capture_number: timelapse capture number (for filename)
    :return:
    """

    path = ''
    filename = ''
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    if record_type == 'photo':
        path = os.path.join(INSTALL_DIRECTORY, 'camera-stills')
        filename = 'Still-{ts}.jpg'.format(ts=timestamp)
    elif record_type == 'timelapse':
        path = os.path.join(INSTALL_DIRECTORY, 'camera-timelapse')
        filename = '{st}-img-{cn:05d}.jpg'.format(st=start_time,
                                                  cn=capture_number)
    elif record_type == 'video':
        path = os.path.join(INSTALL_DIRECTORY, 'camera-video')
        filename = 'Video-{ts}.h264'.format(ts=timestamp)
    path_file = os.path.join(path, filename)

    assure_path_exists(path)

    with picamera.PiCamera() as camera:
        camera.resolution = (1296, 972)
        camera.hflip = settings.hflip
        camera.vflip = settings.vflip
        camera.rotation = settings.rotation
        camera.start_preview()
        time.sleep(2)  # Camera warm-up time

        if record_type in ['photo', 'timelapse']:
            camera.capture(path_file, use_video_port=True)
        elif record_type == 'video':
            camera.start_recording(path_file, format='h264', quality=20)
            camera.wait_recording(duration_sec)
            camera.stop_recording()
        else:
            return

    try:
        set_user_grp(path_file, 'mycodo', 'mycodo')
    except Exception as e:
        logger.error(
            "Exception raised in 'camera_record' when setting user grp: "
            "{err}".format(err=e))
