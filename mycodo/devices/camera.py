# -*- coding: utf-8 -*-
from __future__ import print_function  # In python 2.7

import datetime
import logging
import time

import os
import picamera

from mycodo.config import INSTALL_DIRECTORY
from mycodo.databases.models import Camera
from mycodo.databases.models import Output
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.system_pi import assure_path_exists
from mycodo.utils.system_pi import cmd_output
from mycodo.utils.system_pi import set_user_grp
from mycodo.mycodo_client import DaemonControl

logger = logging.getLogger('mycodo.devices.picamera')


#
# Camera record
#

def camera_record(record_type, unique_id, duration_sec=None, tmp_filename=None):
    """
    Record still image from cameras
    :param record_type:
    :param unique_id:
    :param duration_sec:
    :param tmp_filename:
    :return:
    """
    settings = db_retrieve_table_daemon(Camera, unique_id=unique_id)
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    root_path = os.path.abspath(os.path.join(INSTALL_DIRECTORY, 'cameras'))
    assure_path_exists(root_path)
    camera_path = assure_path_exists(
        os.path.join(root_path, '{uid}'.format(uid=settings.unique_id)))
    if record_type == 'photo':
        save_path = assure_path_exists(os.path.join(camera_path, 'still'))
        filename = 'Still-{cam_id}-{cam}-{ts}.jpg'.format(
            cam_id=settings.id,
            cam=settings.name,
            ts=timestamp).replace(" ", "_")
    elif record_type == 'timelapse':
        save_path = assure_path_exists(os.path.join(camera_path, 'timelapse'))
        start = datetime.datetime.fromtimestamp(
            settings.timelapse_start_time).strftime("%Y-%m-%d_%H-%M-%S")
        filename = 'Timelapse-{cam_id}-{cam}-{st}-img-{cn:05d}.jpg'.format(
            cam_id=settings.id,
            cam=settings.name,
            st=start,
            cn=settings.timelapse_capture_number).replace(" ", "_")
    elif record_type == 'video':
        save_path = assure_path_exists(os.path.join(camera_path, 'video'))
        filename = 'Video-{cam}-{ts}.h264'.format(
            cam=settings.name,
            ts=timestamp).replace(" ", "_")
    else:
        return

    if tmp_filename:
        filename = tmp_filename

    path_file = os.path.join(save_path, filename)


    # Turn on output, if configured
    if settings.relay_id:
        daemon_control = DaemonControl()
        daemon_control.relay_on(settings.relay_id)


    if settings.library == 'picamera':
        # Try 5 times to access the pi camera (in case another process is accessing it)
        for _ in range(5):
            try:
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
                    break
            except picamera.exc.PiCameraMMALError:
                # 'out of resources' error when the camera is already open by picamera
                pass
            time.sleep(1)

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
        if settings.custom_options:
            cmd += " " + settings.custom_options

        out, err, status = cmd_output(cmd, stdout_pipe=False)
        # logger.error("TEST01: {}; {}; {}; {}".format(cmd, out, err, status))

    # Turn off output, if configured
    if settings.relay_id:
        daemon_control.relay_off(settings.relay_id)

    try:
        set_user_grp(path_file, 'mycodo', 'mycodo')
        return save_path, filename
    except Exception as e:
        logger.exception(
            "Exception raised in 'camera_record' when setting user grp: "
            "{err}".format(err=e))
