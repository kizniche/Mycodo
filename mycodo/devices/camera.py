# -*- coding: utf-8 -*-
from __future__ import print_function  # In python 2.7

import cv2
import datetime
import imutils
import io
import logging
import os
import picamera
import threading
import time

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
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    root_path = assure_path_exists(os.path.join(INSTALL_DIRECTORY, 'cameras'))
    camera_path = assure_path_exists(
        os.path.join(root_path, '{id}-{uid}'.format(id=settings.id,
                                                    uid=settings.unique_id)))
    if record_type == 'photo':
        save_path = assure_path_exists(os.path.join(camera_path, 'still'))
        filename = 'Still-{cam_id}-{cam}-{ts}.jpg'.format(
            cam_id=settings.id,
            cam=settings.name,
            ts=timestamp)
    elif record_type == 'timelapse':
        save_path = assure_path_exists(os.path.join(camera_path, 'timelapse'))
        start = datetime.datetime.fromtimestamp(
            settings.timelapse_start_time).strftime("%Y-%m-%d_%H-%M-%S")
        filename = 'Timelapse-{cam_id}-{cam}-{st}-img-{cn:05d}.jpg'.format(
            cam_id=settings.id,
            cam=settings.name,
            st=start,
            cn=settings.timelapse_capture_number)
    elif record_type == 'video':
        save_path = assure_path_exists(os.path.join(camera_path, 'video'))
        filename = 'Video-{cam}-{ts}.h264'.format(
            cam=settings.name,
            ts=timestamp)
    else:
        return

    path_file = os.path.join(save_path, filename)

    if settings.library == 'picamera':
        with picamera.PiCamera() as camera:
            camera.resolution = (settings.width, settings.height)
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

    elif settings.library == 'opencv':
        cap = cv2.VideoCapture(settings.opencv_device)

        # Check if image can be read
        if not cap.read():
            logger.error(
                "Cannot detect USB camera with device '{dev}'".format(
                    dev=settings.opencv_device))
            return

        cap.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, settings.width)
        cap.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, settings.height)
        cap.set(cv2.cv.CV_CAP_PROP_EXPOSURE, settings.exposure)
        cap.set(cv2.cv.CV_CAP_PROP_GAIN, settings.gain)
        cap.set(cv2.cv.CV_CAP_PROP_BRIGHTNESS, settings.brightness)
        cap.set(cv2.cv.CV_CAP_PROP_CONTRAST, settings.contrast)
        cap.set(cv2.cv.CV_CAP_PROP_HUE, settings.hue)
        cap.set(cv2.cv.CV_CAP_PROP_SATURATION, settings.saturation)

        if record_type in ['photo', 'timelapse']:
            edited = False
            ret, img_orig = cap.read()
            img_edited = img_orig.copy()

            if any((settings.hflip, settings.vflip, settings.rotation)):
                edited = True

            if settings.hflip and settings.vflip:
                img_edited = cv2.flip(img_orig, -1)
            elif settings.hflip:
                img_edited = cv2.flip(img_orig, 1)
            elif settings.vflip:
                img_edited = cv2.flip(img_orig, 0)

            if settings.rotation:
                img_edited = imutils.rotate_bound(img_orig, settings.rotation)

            if edited:
                cv2.imwrite(path_file, img_edited)
            else:
                cv2.imwrite(path_file, img_orig)

            cap.release()
        else:
            return
    try:
        set_user_grp(path_file, 'mycodo', 'mycodo')
    except Exception as e:
        logger.error(
            "Exception raised in 'camera_record' when setting user grp: "
            "{err}".format(err=e))


def count_cameras_opencv():
    """ Returns how many cameras are detected with opencv (cv2) """
    num_cameras = 0
    for i in range(10):
        temp_camera = cv2.VideoCapture(i-1)
        ret, img = temp_camera.read()
        if ret:
            num_cameras += 1
    return num_cameras
