# -*- coding: utf-8 -*-
from __future__ import print_function  # In python 2.7

import datetime
import logging
import time

import os
import picamera

from mycodo.config import INSTALL_DIRECTORY
from mycodo.utils.system_pi import assure_path_exists
from mycodo.utils.system_pi import cmd_output
from mycodo.utils.system_pi import set_user_grp

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
    root_path = os.path.abspath(os.path.join(INSTALL_DIRECTORY, 'cameras'))
    assure_path_exists(root_path)
    camera_path = assure_path_exists(
        os.path.join(root_path, '{id}-{uid}'.format(id=settings.id,
                                                    uid=settings.unique_id)))
    if record_type == 'photo':
        save_path = assure_path_exists(os.path.join(camera_path, 'still'))
        filename = u'Still-{cam_id}-{cam}-{ts}.jpg'.format(
            cam_id=settings.id,
            cam=settings.name,
            ts=timestamp).replace(" ", "_")
    elif record_type == 'timelapse':
        save_path = assure_path_exists(os.path.join(camera_path, 'timelapse'))
        start = datetime.datetime.fromtimestamp(
            settings.timelapse_start_time).strftime("%Y-%m-%d_%H-%M-%S")
        filename = u'Timelapse-{cam_id}-{cam}-{st}-img-{cn:05d}.jpg'.format(
            cam_id=settings.id,
            cam=settings.name,
            st=start,
            cn=settings.timelapse_capture_number).replace(" ", "_")
    elif record_type == 'video':
        save_path = assure_path_exists(os.path.join(camera_path, 'video'))
        filename = u'Video-{cam}-{ts}.h264'.format(
            cam=settings.name,
            ts=timestamp).replace(" ", "_")
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

    elif settings.library == 'fswebcam':
        cmd = "/usr/bin/fswebcam --device {dev} --resolution {w}x{h} --set brightness={bt}% " \
              "--no-banner --save {file}".format(dev=settings.device,
                                                 w=settings.width,
                                                 h=settings.height,
                                                 bt=settings.brightness,
                                                 file=path_file)
        if settings.hflip:
            cmd += " --flip h"
        if settings.vflip:
            cmd += " --flip h"
        if settings.rotation:
            cmd += " --rotate {angle}".format(angle=settings.rotation)

        # logger.error(cmd)
        out, err, status = cmd_output(cmd, stdout_pipe=False)
        # logger.error("TEST01: {}; {}; {}".format(out, err, status))

    try:
        set_user_grp(path_file, 'mycodo', 'mycodo')
    except Exception as e:
        logger.exception(
            "Exception raised in 'camera_record' when setting user grp: "
            "{err}".format(err=e))
