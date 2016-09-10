# coding=utf-8

import datetime
import picamera
import time

from system_pi import assure_path_exists
from system_pi import set_user_grp


#
# Camera record
#

def camera_record(install_directory, record_type, duration_sec=None, start_time=None, capture_number=None):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    try:
        if record_type == 'photo' or record_type == 'timelapse':
            if record_type == 'photo':
                path_images = '{}/camera-stills'.format(install_directory)
                still_filename = 'Still-{}.jpg'.format(timestamp)
                output_filepath = '{}/{}'.format(path_images, still_filename)
            elif record_type == 'timelapse':
                path_images = '{}/camera-timelapse'.format(install_directory)
                still_filename = '{}-img-{:05d}.jpg'.format(start_time, capture_number)
                output_filepath = '{}/{}'.format(path_images, still_filename)
            assure_path_exists(path_images)
            with picamera.PiCamera() as camera:
                camera.resolution = (1296, 972)
                camera.hflip = True
                camera.vflip = True
                camera.start_preview()
                time.sleep(2)  # Camera warm-up time
                camera.capture(output_filepath, use_video_port=True)
        elif record_type == 'video':
            path_video = '{}/camera-video'.format(install_directory)
            video_filename = 'Video-{}.h264'.format(timestamp)
            output_filepath = '{}/{}'.format(path_video, video_filename)
            assure_path_exists(path_video)
            with picamera.PiCamera() as camera:
                camera.resolution = (1296, 972)
                camera.hflip = True
                camera.vflip = True
                camera.start_preview()
                time.sleep(2)
                camera.start_recording(output_filepath, format='h264', quality=20)
                camera.wait_recording(duration_sec)
                camera.stop_recording()
    except:
        pass

    try:
        set_user_grp(output_filepath, 'mycodo', 'mycodo')
    except:
        pass
