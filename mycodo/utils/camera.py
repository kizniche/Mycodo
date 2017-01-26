# coding=utf-8
import logging
import datetime
import picamera
import time

from system_pi import (
    assure_path_exists,
    set_user_grp
)

from config import INSTALL_DIRECTORY

logger = logging.getLogger("mycodo.camera")


#
# Camera record
#

def camera_record(record_type, settings, duration_sec=None,
                  start_time=None, capture_number=None):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    path = ''
    path_file = ''
    if record_type == 'photo':
        path = '{}/camera-stills'.format(INSTALL_DIRECTORY)
        filename = 'Still-{}.jpg'.format(timestamp)
        path_file = '{}/{}'.format(path, filename)
    elif record_type == 'timelapse':
        path = '{}/camera-timelapse'.format(INSTALL_DIRECTORY)
        filename = '{}-img-{:05d}.jpg'.format(start_time, capture_number)
        path_file = '{}/{}'.format(path, filename)
    elif record_type == 'video':
        path = '{}/camera-video'.format(INSTALL_DIRECTORY)
        filename = 'Video-{}.h264'.format(timestamp)
        path_file = '{}/{}'.format(path, filename)

    assure_path_exists(path)

    with picamera.PiCamera() as camera:
        camera.resolution = (1296, 972)
        camera.hflip = settings.hflip
        camera.vflip = settings.vflip
        camera.rotation = settings.rotation
        camera.start_preview()
        time.sleep(2)  # Camera warm-up time

        if record_type == 'photo' or record_type == 'timelapse':
            camera.capture(path_file, use_video_port=True)
        elif record_type == 'video':
            camera.start_recording(path_file, format='h264', quality=20)
            camera.wait_recording(duration_sec)
            camera.stop_recording()

    try:
        set_user_grp(path_file, 'mycodo', 'mycodo')
    except Exception as e:
        logger.error(
            "Exception raised in 'camera_record' when setting user grp: "
            "{err}".format(err=e))
