# coding=utf-8
#
#  camera_libcamera.py - Capture image using libcamera library
#
#  Copyright (C) 2015-2020 Kyle T. Gabriel <mycodo@kylegabriel.com>
#
#  This file is part of Mycodo
#
#  Mycodo is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Mycodo is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Mycodo. If not, see <http://www.gnu.org/licenses/>.
#
#  Contact at kylegabriel.com
#
import os
import time
from datetime import datetime as dt

from flask_babel import lazy_gettext

from mycodo.config import PATH_CAMERAS
from mycodo.databases.models import CustomController
from mycodo.functions.base_function import AbstractFunction
from mycodo.utils.camera_functions import get_camera_function_image_info
from mycodo.utils.constraints_pass import constraints_pass_positive_value
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.system_pi import assure_path_exists, cmd_output


def function_status(function_id):
    return_str = {
        'string_status': generate_latest_media_html(function_id),
        'error': []
    }
    return return_str

def generate_latest_media_html(unique_id):
    str_last_media = ""

    (latest_img_still_ts,
    latest_img_still_size,
    latest_img_still,
    latest_img_video_ts,
    latest_img_video_size,
    latest_img_video,
    latest_img_tl_ts,
    latest_img_tl_size,
    latest_img_tl,
    time_lapse_imgs) = get_camera_function_image_info(unique_id)

    if latest_img_tl_ts:
        last_tl = lazy_gettext('Last Timelapse Image')
        str_last_media += f'<div style="padding-top: 0.5em">{last_tl}: {latest_img_tl_ts} ({latest_img_tl_size})<br/><a href="/camera/{unique_id}/timelapse/{latest_img_tl}" target="_blank"><img style="max-width: 100%" src="/camera/{unique_id}/timelapse/{latest_img_tl}"></a></div>'

    if latest_img_still_ts:
        last_still = lazy_gettext('Last Still Image')
        str_last_media += f'<div style="padding-top: 0.5em">{last_still}: {latest_img_still_ts} ({latest_img_still_size})<br/><a href="/camera/{unique_id}/still/{latest_img_still}" target="_blank"><img style="max-width: 100%" src="/camera/{unique_id}/still/{latest_img_still}"></a></div>'
    
    if latest_img_video_ts:
        last_video = lazy_gettext('Last Video')
        str_last_media += f'<div style="padding-top: 0.5em">{last_video}: {latest_img_video_ts} ({latest_img_video_size}) <a href="/camera/{unique_id}/video/{latest_img_video}">Download</a>'

        if latest_img_video.endswith("mp4"):
            str_last_media += f'<br/><video controls style="max-width: 100%"><source src="/camera/{unique_id}/video/{latest_img_video}" type="video/mp4"></video>'

        str_last_media += '</div>'
    
    return str_last_media

FUNCTION_INFORMATION = {
    'function_name_unique': 'CAMERA_LIBCAMERA',
    'function_name': '{}: libcamera: {}/{}'.format(lazy_gettext("Camera"), lazy_gettext("Image"), lazy_gettext("Video")),
    'function_name_short': '{} libcamera'.format(lazy_gettext("Camera")),
    'modify_settings_without_deactivating': True,
    'camera_image': True,
    'camera_video': True,
    'camera_stream': False,
    'function_status': function_status,

    'message': 'NOTE: THIS IS CURRENTLY EXPERIMENTAL - USE AT YOUR OWN RISK UNTIL THIS NOTICE IS REMOVED. Capture images and videos from a camera using libcamera-still and libcamera-vid. The Function must be activated in order to capture still and timelapse images and use the Camera Widget.',

    'options_enabled': [
        'function_status'
    ],
    'options_disabled': [
        'measurements_select',
        'measurements_configure'
    ],

    'dependencies_module': [
        ('apt', 'libcamera-apps', 'libcamera-apps'),
        ('apt', 'ffmpeg', 'ffmpeg'),
    ],

    'custom_commands': [
        {
            'id': 'capture_image',
            'type': 'button',
            'wait_for_return': True,
            'name': 'Capture Image',
            'phrase': "Acquire a still image from the camera"
        },
        {
            'type': 'message',
            'default_value': """To capture a video, enter the duration and press Capture Video."""
        },
        {
            'id': 'vid_duration_sec',
            'type': 'integer',
            'default_value': 5,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Video Duration (Seconds)',
            'phrase': 'How long to record the video'
        },
        {
            'id': 'capture_video',
            'type': 'button',
            'wait_for_return': False,
            'name': 'Capture Video',
            'phrase': "Cpature a video for the specific duration"
        },
        {
            'type': 'message',
            'default_value': """To start a timelapse, enter the duration and period and press Start Timelapse."""
        },
        {
            'id': 'tl_duration_sec',
            'type': 'integer',
            'default_value': 2592000,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Timelapse Duration (Seconds)',
            'phrase': 'How long the timelapse will run'
        },
        {
            'id': 'tl_period_sec',
            'type': 'integer',
            'default_value': 600,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Timelapse Period (Seconds)',
            'phrase': 'How often to take a timelapse photo'
        },
        {
            'id': 'timelapse_start',
            'type': 'button',
            'wait_for_return': True,
            'name': 'Start Timelapse',
            'phrase': "Start a timelapse with the provided options"
        },
        {
            'type': 'message',
            'default_value': """To stop an active timelapse, press Stop Timelapse."""
        },
        {
            'id': 'timelapse_stop',
            'type': 'button',
            'wait_for_return': True,
            'name': 'Stop Timelapse',
            'phrase': "Stop an active timelapse"
        },
        {
            'type': 'message',
            'default_value': """To pause or resume an active timelapse, press Pause Timelapse or Resume Timelapse."""
        },
        {
            'id': 'timelapse_pause',
            'type': 'button',
            'wait_for_return': True,
            'name': 'Pause Timelapse',
            'phrase': "Pause an active timelapse"
        },
        {
            'id': 'timelapse_resume',
            'type': 'button',
            'wait_for_return': True,
            'name': 'Resume Timelapse',
            'phrase': "Resume an active timelapse"
        }
    ],

    'custom_options': [
        {
            'id': 'period_status',
            'type': 'integer',
            'default_value': 60,
            'required': True,
            'name': 'Status Period (seconds)',
            'phrase': 'The duration (seconds) to update the Function status on the UI'
        },
        {
            'type': 'message',
            'default_value': """Image options."""
        },
        {
            'id': 'custom_path_still',
            'type': 'text',
            'default_value': '',
            'required': False,
            'name': "Custom Image Path",
            'phrase': "Set a non-default path for still images to be saved"
        },
        {
            'id': 'custom_path_timelapse',
            'type': 'text',
            'default_value': '',
            'required': False,
            'name': "Custom Timelapse Path",
            'phrase': "Set a non-default path for timelapse images to be saved"
        },
        {
            'id': 'image_extension',
            'type': 'select',
            'default_value': 'jpg',
            'required': True,
            'options_select': [
                ('jpg', 'JPG'),
                ('png', 'PNG'),
                ('bmp', 'BMP'),
                ('rgb', 'RGB'),
                ('yuv420', 'YUV420')
            ],
            'name': 'Image Extension',
            'phrase': 'The file type/format to save images'
        },
        {
            'id': 'image_width',
            'type': 'integer',
            'default_value': 720,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': "{}: {}: {}".format(lazy_gettext('Image'), lazy_gettext('Resolution'), lazy_gettext('Width')),
            'phrase': "The width of still images"
        },
        {
            'id': 'image_height',
            'type': 'integer',
            'default_value': 480,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': "{}: {}: {}".format(lazy_gettext('Image'), lazy_gettext('Resolution'), lazy_gettext('Height')),
            'phrase': "The height of still images"
        },
        {
            'id': 'image_brightness',
            'type': 'float',
            'default_value': 0.0,
            'required': True,
            'name': "{}".format(lazy_gettext('Brightness')),
            'phrase': "The brightness of still images (-1 to 1)"
        },
        {
            'id': 'image_contrast',
            'type': 'float',
            'default_value': 1.0,
            'required': True,
            'name': "{}: {}".format(lazy_gettext('Image'), lazy_gettext('Contrast')),
            'phrase': "The contrast of still images. Larger values produce images with more contrast."
        },
        {
            'id': 'image_saturation',
            'type': 'float',
            'default_value': 1.0,
            'required': True,
            'name': "{}".format(lazy_gettext('Saturation')),
            'phrase': "The saturation of still images. Larger values produce more saturated colours; 0.0 produces a greyscale image."
        },
        {
            'id': 'image_sharpness',
            'type': 'float',
            'default_value': 0.0,
            'required': True,
            'name': "{}".format(lazy_gettext('Sharpness')),
            'phrase': "The sharpness of still images. Larger values produce more saturated colours; 0.0 produces a greyscale image."
        },
        {
            'id': 'image_shutter_speed_us',
            'type': 'integer',
            'default_value': 0,
            'required': True,
            'name': "{} ({})".format(lazy_gettext('Shutter Speed'), lazy_gettext('Microseconds')),
            'phrase': "The shutter speed, in microseconds. 0 disables and returns to auto exposure."
        },
        {
            'id': 'image_gain',
            'type': 'float',
            'default_value': 1.0,
            'required': True,
            'name': "{}".format(lazy_gettext('Gain')),
            'phrase': "The gain of still images."
        },
        {
            'id': 'image_awb',
            'type': 'select',
            'default_value': 'auto',
            'required': True,
            'options_select': [
                ('auto', 'Auto'),
                ('incandescent', 'Incandescent'),
                ('tungsten', 'Tungsten'),
                ('fluorescent', 'Fluorescent'),
                ('indoor', 'Indoor'),
                ('daylight', 'Daylight'),
                ('cloudy', 'Cloudy'),
                ('custom', 'Custom')
            ],
            'name': '{}: Auto'.format(lazy_gettext('White Balance')),
            'phrase': 'The white balance of images'
        },
        {
            'id': 'image_awb_gain_red',
            'type': 'float',
            'default_value': 0.0,
            'required': True,
            'name': "{}: Red Gain".format(lazy_gettext('White Balance')),
            'phrase': "The red gain of white balance for still images (disabled Auto White Balance if red and blue are not set to 0)"
        },
        {
            'id': 'image_awb_gain_blue',
            'type': 'float',
            'default_value': 0.0,
            'required': True,
            'name': "{}: Blue Gain".format(lazy_gettext('White Balance')),
            'phrase': "The red gain of white balance for still images (disabled Auto White Balance if red and blue are not set to 0)"
        },
        {
            'id': 'image_hflip',
            'type': 'bool',
            'default_value': False,
            'name': 'Flip Horizontally',
            'phrase': 'Flip the image horizontally.'
        },
        {
            'id': 'image_vflip',
            'type': 'bool',
            'default_value': False,
            'name': 'Flip Vertically',
            'phrase': 'Flip the image vertically.'
        },
        {
            'id': 'image_rotate',
            'type': 'integer',
            'default_value': 0,
            'required': True,
            'name': "{} ({})".format(lazy_gettext('Rotate'), lazy_gettext('Degrees')),
            'phrase': "Rotate the image."
        },
        {
            'id': 'image_custom_options',
            'type': 'text',
            'default_value': '',
            'required': False,
            'name': "Custom libcamera-still Options",
            'phrase': "Pass custom options to the libcamera-still command."
        },
        {
            'type': 'message',
            'default_value': """Video options."""
        },
        {
            'id': 'custom_path_video',
            'type': 'text',
            'default_value': '',
            'required': False,
            'name': "Custom Video Path",
            'phrase': "Set a non-default path for videos to be saved"
        },
        {
            'id': 'video_extension',
            'type': 'select',
            'default_value': 'h264-mp4',
            'required': True,
            'options_select': [
                ('h264-mp4', 'H264 -> MP4 (with ffmpeg)'),
                ('h264', 'H264'),
                ('mjpeg', 'MJPEG'),
                ('yuv420', 'YUV420')
            ],
            'name': 'Video Extension',
            'phrase': 'The file type/format to save videos'
        },
        {
            'id': 'video_width',
            'type': 'integer',
            'default_value': 720,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': "{}: {}: {}".format(lazy_gettext('Video'), lazy_gettext('Resolution'), lazy_gettext('Width')),
            'phrase': "The width of videos"
        },
        {
            'id': 'video_height',
            'type': 'integer',
            'default_value': 480,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': "{}: {}: {}".format(lazy_gettext('Video'), lazy_gettext('Resolution'), lazy_gettext('Height')),
            'phrase': "The height of videos"
        },
        {
            'id': 'video_custom_options',
            'type': 'text',
            'default_value': '',
            'required': False,
            'name': "Custom libcamera-vid Options",
            'phrase': "Pass custom options to the libcamera-vid command."
        },
    ]
}


class CustomModule(AbstractFunction):
    """
    Class to operate custom controller
    """
    def __init__(self, function, testing=False):
        super().__init__(function, testing=testing, name=__name__)

        self.timer_loop = time.time()

        self.tl_active = None
        self.tl_pause = None
        self.tl_duration_sec = None
        self.tl_period_sec = None
        self.tl_capture_number = None
        self.tl_start_epoch = None
        self.tl_start_str = None
        self.tl_end_str = None
        self.still_last_file = None
        self.still_last_ts = None
        self.video_last_file = None
        self.video_last_ts = None
        self.tl_last_file = None
        self.tl_last_ts = None
        self.image_awb_gain_red = None
        self.image_awb_gain_blue = None
        self.image_hflip = None
        self.image_vflip = None

        # Initialize custom options
        self.custom_path_still = None
        self.custom_path_video = None
        self.custom_path_timelapse = None
        self.image_extension = None
        self.image_width = None
        self.image_height = None
        self.video_extension = None
        self.video_width = None
        self.video_height = None
        self.image_brightness = None
        self.image_contrast = None
        self.image_saturation = None
        self.image_sharpness = None
        self.image_shutter_speed_us = None
        self.image_gain = None
        self.image_awb = None
        self.image_rotate = None
        self.image_custom_options = None
        self.video_custom_options = None

        # Set custom options
        self.set_custom_options()

        if not testing:
            self.try_initialize()

    def initialize(self):
        self.timer_loop = self.get_custom_option("timer_loop")
        if self.timer_loop is None:
            self.timer_loop = self.set_custom_option("timer_loop", time.time())
        self.tl_duration_sec = self.get_custom_option("tl_duration_sec")
        self.tl_period_sec = self.get_custom_option("tl_period_sec")
        self.tl_capture_number = self.get_custom_option("tl_capture_number")
        self.tl_start_epoch = self.get_custom_option("tl_start_epoch")
        self.tl_start_str = self.get_custom_option("tl_start_str")
        self.tl_end_str = self.get_custom_option("tl_end_str")
        self.still_last_file = self.get_custom_option("still_last_file")
        self.still_last_ts = self.get_custom_option("still_last_ts")
        self.video_last_file = self.get_custom_option("video_last_file")
        self.video_last_ts = self.get_custom_option("video_last_ts")
        self.tl_last_file = self.get_custom_option("tl_last_file")
        self.tl_last_ts = self.get_custom_option("tl_last_ts")
        self.tl_pause = self.get_custom_option("tl_pause")
        self.tl_active = self.get_custom_option("tl_active")

        self.logger.debug(f"Starting with tl_active {self.tl_active}, tl_pause {self.tl_pause}")
    
    def set_custom_options(self):
        custom_function = db_retrieve_table_daemon(
            CustomController, unique_id=self.unique_id)
        self.setup_custom_options(
            FUNCTION_INFORMATION['custom_options'], custom_function)

    def loop(self):
        if not self.tl_active or self.timer_loop > time.time():
            return

        while self.timer_loop < time.time():
            self.timer_loop += self.tl_period_sec
        self.set_custom_option("timer_loop", self.timer_loop)

        if self.tl_pause:
            return

        # Check if timelapse has ended:
        if self.tl_start_epoch + self.tl_duration_sec < time.time():
            self.timelapse_stop()
            return

        self.capture("timelapse")
        self.tl_capture_number = self.set_custom_option(
            "tl_capture_number", self.tl_capture_number + 1)

    def capture(self, record_type, duration_sec=None, tmp_filename=None):
        try:
            self.set_custom_options()
            now = time.time()
            date = dt.fromtimestamp(now).strftime('%Y-%m-%d_%H-%M-%S')

            camera_path = assure_path_exists(
                os.path.join(PATH_CAMERAS, self.unique_id))

            if record_type == 'photo':
                if tmp_filename:
                    save_path = "/tmp"
                elif self.custom_path_still:
                    save_path = self.custom_path_still
                else:
                    save_path = assure_path_exists(
                        os.path.join(camera_path, 'still'))
                filename = f'Still-{date}.{self.image_extension}'.replace(" ", "_")

            elif record_type == 'video':
                if tmp_filename:
                    save_path = "/tmp"
                elif self.custom_path_video:
                    save_path = self.custom_path_video
                else:
                    save_path = assure_path_exists(
                        os.path.join(camera_path, 'video'))
                if self.video_extension == 'h264-mp4':
                    filename = f'Video-{date}.h264'.replace(" ", "_")
                else:
                    filename = f'Video-{date}.{self.video_extension}'.replace(" ", "_")

            elif record_type == 'timelapse':
                if tmp_filename:
                    save_path = "/tmp"
                elif self.custom_path_timelapse:
                    save_path = self.custom_path_timelapse
                else:
                    save_path = assure_path_exists(
                        os.path.join(camera_path, 'timelapse'))
                filename = f'Timelapse-{self.tl_start_str}-img-{self.tl_capture_number:06d}.{self.image_extension}'.replace(" ", "_")

            assure_path_exists(save_path)

            if tmp_filename:
                filename = tmp_filename

            path_file = os.path.join(save_path, filename)

            self.logger.debug(f"Capturing {record_type} to {path_file} at {now:.0f}")

            if not os.path.exists("/usr/bin/libcamera-still"):
                self.logger.error("/usr/bin/libcamera-still not found")
                return None, None
            elif not os.path.exists("/usr/bin/libcamera-vid"):
                self.logger.error("/usr/bin/libcamera-vid not found")
                return None, None

            if record_type in ['photo', 'timelapse']:
                cmd = f"/usr/bin/libcamera-still " \
                      f"--nopreview -o {path_file} " \
                      f"--width {self.image_width} " \
                      f"--height {self.image_height} "

                if self.image_brightness is not None:
                    cmd += f" --brightness {self.image_brightness:.2f}"
                if self.image_contrast is not None:
                    cmd += f" --contrast {self.image_contrast:.2f}"
                if self.image_saturation is not None:
                    cmd += f" --saturation {self.image_saturation:.2f}"
                if self.image_sharpness is not None:
                    cmd += f" --sharpness {self.image_sharpness:.2f}"
                if self.image_gain:
                    cmd += f" --gain {self.image_gain:.2f}"
                if self.image_awb:
                    cmd += f" --awb {self.image_awb}"
                if self.image_awb_gain_red != 0 or self.image_awb_gain_blue != 0:
                    cmd += f" --awbgains {self.image_awb_gain_red:.2f},{self.image_awb_gain_blue:.2f}"
                if self.image_hflip:
                    cmd += " --hflip 1"
                if self.image_vflip:
                    cmd += " --vflip 1"
                if self.image_rotate:
                    cmd += f" --rotation {self.image_rotate}"
                
                if self.image_extension:
                    cmd += f" --encoding {self.image_extension}"
                if self.image_shutter_speed_us:
                    cmd += f" --shutter {self.image_shutter_speed_us}"
            elif record_type == 'video':
                cmd = f"/usr/bin/libcamera-vid " \
                      f"--timeout {int(duration_sec * 1000)} " \
                      f"--nopreview -o {path_file} " \
                      f"--width {self.video_width} " \
                      f"--height {self.video_height} "
                if self.video_extension:
                    if self.video_extension == 'h264-mp4':
                        cmd += f" --codec h264 "
                    else:
                        cmd += f" --codec {self.video_extension} "

            if record_type in ['photo', 'timelapse'] and self.image_custom_options:
                cmd += f" {self.image_custom_options}"
            elif record_type == 'video' and self.video_custom_options:
                cmd += f" {self.video_custom_options}"

            out, err, status = cmd_output(cmd, stdout_pipe=False, user='root')
            self.logger.debug(
                f"Camera debug message: cmd: {cmd}; out: {out}; error: {err}; status: {status}")

            if record_type == 'video' and self.video_extension == 'h264-mp4':
                out_file = f'Video-{date}.mp4'.replace(" ", "_")
                out_path = os.path.join(save_path, out_file)
                cmd = f'ffmpeg -framerate 24 -i {path_file} -c copy {out_path}'
                out, err, status = cmd_output(cmd, stdout_pipe=False, user='root')
                self.logger.debug(
                    f"ffmpeg debug message: cmd: {cmd}; out: {out}; error: {err}; status: {status}")
                filename = out_file

            if tmp_filename:
                # Don't save tmp files as last file in the database
                pass
            elif record_type == 'photo':
                self.still_last_file = self.set_custom_option("still_last_file", filename)
                self.still_last_ts = self.set_custom_option("still_last_ts", now)
            elif record_type == 'video':
                self.video_last_file = self.set_custom_option("video_last_file", filename)
                self.video_last_ts = self.set_custom_option("video_last_ts", now)
            elif record_type == 'timelapse':
                self.tl_last_file = self.set_custom_option("tl_last_file", filename)
                self.tl_last_ts = self.set_custom_option("tl_last_ts", now)
        except:
            self.logger.exception("libcamera")

        return save_path, filename

    def capture_image(self, args_dict=None):
        """Capture a still image"""
        tmp_filename = None
        if "tmp_filename" in args_dict:
            tmp_filename = args_dict["tmp_filename"]
        path, filename = self.capture("photo", tmp_filename=tmp_filename)
        response = {
            'message': "Image captured.",
            'path': path,
            'filename': filename
        }
        return response

    def capture_video(self, args_dict=None):
        """Capture a video"""
        if 'vid_duration_sec' not in args_dict or 'vid_duration_sec' not in args_dict:
            self.logger.error("Invalid video duration.")
            return
        self.capture("video", duration_sec=args_dict['vid_duration_sec'])
        return "Video capturing in background."

    def timelapse_start(self, args_dict=None):
        """Start a timelapse."""
        now = time.time()
        if self.tl_active:
            self.logger.error("Cannot activate timelapse, it is already active.")
            return
        if 'tl_duration_sec' not in args_dict or 'tl_period_sec' not in args_dict:
            self.logger.error("Invalid timelapse duration or period.")
            return
        self.logger.debug(
            f"Timelapse started for {args_dict['tl_duration_sec']} seconds "
            f"at a period of {args_dict['tl_period_sec']} seconds.")
        self.tl_duration_sec = self.set_custom_option("tl_duration_sec", args_dict['tl_duration_sec'])
        self.tl_period_sec = self.set_custom_option("tl_period_sec", args_dict['tl_period_sec'])
        self.tl_capture_number = self.set_custom_option("tl_capture_number", 1)
        self.tl_start_epoch = self.set_custom_option("tl_start_epoch", now)
        start_str = dt.fromtimestamp(
            self.tl_start_epoch).strftime("%Y-%m-%d %H:%M:%S")
        self.tl_start_str = self.set_custom_option("tl_start_str", start_str)
        end_str = dt.fromtimestamp(
            self.tl_start_epoch + self.tl_duration_sec).strftime("%Y-%m-%d %H:%M:%S")
        self.tl_end_str = self.set_custom_option("tl_end_str", end_str)
        self.tl_pause = self.set_custom_option("tl_pause", False)
        self.tl_active = self.set_custom_option("tl_active", True)
        self.timer_loop = now
        return "Timelapse started."

    def timelapse_pause(self, args_dict=None):
        """Pause a timelapse."""
        if self.tl_pause:
            self.logger.error("Cannot pause timelapse, it is already paused.")
            return
        self.logger.debug("Timelapse paused.")
        self.tl_pause = self.set_custom_option("tl_pause", True)
        return "Timelapse paused."
    
    def timelapse_resume(self, args_dict=None):
        """Resume a timelapse."""
        if not self.tl_pause:
            self.logger.error("Cannot resume timelapse, it is not paused.")
            return
        self.logger.debug("Timelapse resumed.")
        self.tl_pause = self.set_custom_option("tl_pause", False)
        return "Timelapse resumed."

    def timelapse_stop(self, args_dict=None):
        """Stop a timelapse."""
        if not self.tl_active:
            self.logger.error("Cannot stop timelapse, it is not active.")
            return
        self.logger.debug("Timelapse stopped.")
        self.tl_pause = self.set_custom_option("tl_pause", False)
        self.tl_active = self.set_custom_option("tl_active", False)
        return "Timelapse stopped."

    def function_status(self):
        now = time.time()

        if self.tl_active:
            if self.tl_pause:
                str_timelapse = f"Time-lapse Status: PAUSED"
            else:
                str_timelapse = f"Time-lapse Status: ACTIVE"

            str_timelapse += f"<br>Start: {self.tl_start_str}" \
                             f"<br>End: {self.tl_end_str}" \
                             f"<br>Duration (Seconds): {self.tl_duration_sec}" \
                             f"<br>Period (Seconds): {self.tl_period_sec}" \
                             f"<br>Next Capture Number: {self.tl_capture_number}"

            if not self.tl_pause:
                next_capture_str = dt.fromtimestamp(
                    self.timer_loop).strftime("%Y-%m-%d %H:%M:%S")
                next_sec = ""
                if self.timer_loop > now:
                    next_sec = f" ({self.timer_loop - now:.0f} seconds)"
                str_timelapse += f"<br>Next Capture Time: {next_capture_str}{next_sec}"
        else:
            str_timelapse = "Time-lapse Status: INACTIVE"

        return_str = {
            'string_status': str_timelapse,
            'error': []
        }
        return return_str
