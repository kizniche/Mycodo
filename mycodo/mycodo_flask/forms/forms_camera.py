# -*- coding: utf-8 -*-
#
# forms_camera.py - Miscellaneous Flask Forms
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import DecimalField
from wtforms import IntegerField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import validators
from wtforms import widgets
from wtforms.widgets import NumberInput

from mycodo.config_translations import TRANSLATIONS


class Camera(FlaskForm):
    camera_id = StringField('Camera ID', widget=widgets.HiddenInput())
    name = StringField(TRANSLATIONS['name']['title'])
    library = StringField(lazy_gettext('Library'))
    device = StringField(lazy_gettext('Device'))

    capture_still = SubmitField(lazy_gettext('Capture Still'))
    start_timelapse = SubmitField(lazy_gettext('Start Timelapse'))
    pause_timelapse = SubmitField(lazy_gettext('Pause Timelapse'))
    resume_timelapse = SubmitField(lazy_gettext('Resume Timelapse'))
    stop_timelapse = SubmitField(lazy_gettext('Stop Timelapse'))
    timelapse_interval = DecimalField(
        "{} ({})".format(lazy_gettext('Interval'), lazy_gettext('Seconds')),
        validators=[validators.NumberRange(
            min=0,
            message=lazy_gettext('Photo Interval must be a positive value')
        )],
        widget=NumberInput(step='any')
    )
    timelapse_runtime_sec = DecimalField(
        "{} ({})".format(lazy_gettext('Run Time'), lazy_gettext('Seconds')),
        validators=[validators.NumberRange(
            min=0,
            message=lazy_gettext('Total Run Time must be a positive value')
        )],
        widget=NumberInput(step='any')
    )
    start_stream = SubmitField(lazy_gettext('Start Stream'))
    stop_stream = SubmitField(lazy_gettext('Stop Stream'))

    opencv_device = IntegerField(
        lazy_gettext('OpenCV Device'), widget=NumberInput())
    hflip = BooleanField(lazy_gettext('Flip image horizontally'))
    vflip = BooleanField(lazy_gettext('Flip image vertically'))
    rotation = IntegerField(
        lazy_gettext('Rotate Image'), widget=NumberInput())
    brightness = DecimalField(
        lazy_gettext('Brightness'), widget=NumberInput(step='any'))
    contrast = DecimalField(
        lazy_gettext('Contrast'), widget=NumberInput(step='any'))
    exposure = DecimalField(
        lazy_gettext('Exposure'), widget=NumberInput(step='any'))
    gain = DecimalField(
        lazy_gettext('Gain'), widget=NumberInput(step='any'))
    hue = DecimalField(
        lazy_gettext('Hue'), widget=NumberInput(step='any'))
    saturation = DecimalField(
        lazy_gettext('Saturation'), widget=NumberInput(step='any'))
    white_balance = DecimalField(
        lazy_gettext('White Balance'), widget=NumberInput(step='any'))
    custom_options = StringField(lazy_gettext('Custom Options'))
    output_id = StringField(TRANSLATIONS['output']['title'])
    output_duration = DecimalField(
        '{} ({})'.format(TRANSLATIONS['duration']['title'],
                         TRANSLATIONS['output']['title']),
        widget=NumberInput(step='any'))
    cmd_pre_camera = StringField(lazy_gettext('Pre Command'))
    cmd_post_camera = StringField(lazy_gettext('Post Command'))
    path_still = StringField(lazy_gettext('Still Image Path'))
    path_timelapse = StringField(lazy_gettext('Timelapse Path'))
    path_video = StringField(lazy_gettext('Video Path'))
    camera_add = SubmitField(TRANSLATIONS['add']['title'])
    camera_mod = SubmitField(TRANSLATIONS['save']['title'])
    camera_del = SubmitField(TRANSLATIONS['delete']['title'])
    hide_still = BooleanField(lazy_gettext('Hide Last Still'))
    hide_timelapse = BooleanField(lazy_gettext('Hide Last Timelapse'))
    show_preview = BooleanField(lazy_gettext('Show Preview'))
    output_format = StringField(lazy_gettext('Output Format'))

    # Resolutions
    width = IntegerField(
        lazy_gettext('Still Image Width'), widget=NumberInput())
    height = IntegerField(
        lazy_gettext('Still Image Height'), widget=NumberInput())
    resolution_stream_width = IntegerField(
        lazy_gettext('Stream Width'), widget=NumberInput())
    resolution_stream_height = IntegerField(
        lazy_gettext('Stream Height'), widget=NumberInput())
    stream_fps = IntegerField(
        lazy_gettext('Stream Frames Per Second'), widget=NumberInput())

    # Picamera
    picamera_shutter_speed = IntegerField(lazy_gettext('Shutter Speed'))
    picamera_sharpness = IntegerField(lazy_gettext('Sharpness'))
    picamera_iso = StringField(lazy_gettext('ISO'))
    picamera_awb = StringField(lazy_gettext('Auto White Balance'))
    picamera_awb_gain_red = DecimalField(
        lazy_gettext('AWB Gain Red'), widget=NumberInput(step='any'))
    picamera_awb_gain_blue = DecimalField(
        lazy_gettext('AWB Gain Blue'), widget=NumberInput(step='any'))
    picamera_exposure_mode = StringField(lazy_gettext('Exposure Mode'))
    picamera_meter_mode = StringField(lazy_gettext('Meter Mode'))
    picamera_image_effect = StringField(lazy_gettext('Image Effect'))

    # HTTP Address
    url_still = StringField(lazy_gettext('Still HTTP Address'))
    url_stream = StringField(lazy_gettext('Stream HTTP Address'))
    json_headers = StringField(lazy_gettext('Headers (JSON)'))

    # Timelapse video generation
    timelapse_image_set = StringField(lazy_gettext('Image Set'))
    timelapse_codec = StringField(lazy_gettext('Codec'))
    timelapse_fps = IntegerField(lazy_gettext('Frames Per Second'))
    timelapse_generate = SubmitField(lazy_gettext('Generate Video'))
