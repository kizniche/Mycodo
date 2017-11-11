# -*- coding: utf-8 -*-
from __future__ import print_function  # In python 2.7

import cv2
import datetime
import imutils
import logging
import os
import picamera
import time

from mycodo.utils.system_pi import (
    assure_path_exists,
    set_user_grp
)

from mycodo.config import INSTALL_DIRECTORY

logger = logging.getLogger('mycodo.devices.picamera')


#
# Camera record
#

def camera_record(record_type, settings, duration_sec=None):
    """
    Record still/timelapse images, and video

    :param record_type: 'photo', 'timelapse', or 'video'
    :param settings: picamera settings object
    :param duration_sec: video duration
    :return:
    """
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    root_path = assure_path_exists(os.path.join(INSTALL_DIRECTORY, 'cameras'))
    camera_path = assure_path_exists(
        os.path.join(root_path, '{id}-{uid}'.format(id=settings.id,
                                                    uid=settings.unique_id)))
    if record_type == 'photo':
        save_path = assure_path_exists(os.path.join(camera_path, 'still'))
        filename = u'Still-{cam_id}-{cam}-{ts}.jpg'.format(
            cam_id=settings.id,
            cam=settings.name,
            ts=timestamp)
    elif record_type == 'timelapse':
        save_path = assure_path_exists(os.path.join(camera_path, 'timelapse'))
        start = datetime.datetime.fromtimestamp(
            settings.timelapse_start_time).strftime("%Y-%m-%d_%H-%M-%S")
        filename = u'Timelapse-{cam_id}-{cam}-{st}-img-{cn:05d}.jpg'.format(
            cam_id=settings.id,
            cam=settings.name,
            st=start,
            cn=settings.timelapse_capture_number)
    elif record_type == 'video':
        save_path = assure_path_exists(os.path.join(camera_path, 'video'))
        filename = u'Video-{cam}-{ts}.h264'.format(
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
            camera.brightness = int(settings.brightness)
            camera.contrast = int(settings.contrast)
            camera.exposure_compensation = int(settings.exposure)
            camera.saturation = int(settings.saturation)
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

        # Discard a few frames to allow camera to adjust to settings
        for _ in range(2):
            cap.read()

        if record_type in ['photo', 'timelapse']:
            edited = False
            _, img_orig = cap.read()
            cap.release()

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

        elif record_type == 'video':
            # TODO: opencv video recording is currently not working. No idea why.
            try:
                cap = cv2.VideoCapture(settings.opencv_device)
                fourcc = cv2.cv.CV_FOURCC('X', 'V', 'I', 'D')
                resolution = (settings.width, settings.height)
                out = cv2.VideoWriter(path_file, fourcc, 20.0, resolution)

                time_end = time.time() + duration_sec
                while cap.isOpened() and time.time() < time_end:
                    ret, frame = cap.read()
                    if ret:
                        # write the frame
                        out.write(frame)
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            break
                    else:
                        break
                cap.release()
                out.release()
                cv2.destroyAllWindows()
            except Exception as e:
                logger.exception(
                    "Exception raised while recording video: "
                    "{err}".format(err=e))
        else:
            return
    try:
        set_user_grp(path_file, 'mycodo', 'mycodo')
    except Exception as e:
        logger.exception(
            "Exception raised in 'camera_record' when setting user grp: "
            "{err}".format(err=e))


def count_cameras_opencv():
    """ Returns how many cameras are detected with opencv (cv2) """
    max_tested = 100
    for i in range(max_tested):
        temp_camera = cv2.VideoCapture(i)
        if temp_camera.isOpened():
            temp_camera.release()
            continue
        return i
