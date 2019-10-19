# -*- coding: utf-8 -*-
import logging

import sqlalchemy
from flask import flash
from flask import redirect
from flask import url_for

from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import Camera
from mycodo.mycodo_client import DaemonControl
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.mycodo_flask.utils.utils_general import flash_success_errors
from mycodo.utils.database import db_retrieve_table

logger = logging.getLogger(__name__)


def camera_add(form_camera):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['add']['title'],
        controller=TRANSLATIONS['camera']['title'])
    error = []

    new_camera = Camera()
    if Camera.query.filter(Camera.name == form_camera.name.data).count():
        flash("You must choose a unique name", "error")
    new_camera.name = form_camera.name.data
    new_camera.library = form_camera.library.data
    if form_camera.library.data == 'fswebcam':
        new_camera.device = '/dev/video0'
        new_camera.brightness = 50
    elif form_camera.library.data == 'picamera':
        new_camera.brightness = 50
        new_camera.contrast = 0.0
        new_camera.exposure = 0.0
        new_camera.saturation = 0.0
    if not error:
        try:
            new_camera.save()
        except sqlalchemy.exc.OperationalError as except_msg:
            error.append(except_msg)
        except sqlalchemy.exc.IntegrityError as except_msg:
            error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_camera'))


def camera_mod(form_camera):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['modify']['title'],
        controller=TRANSLATIONS['camera']['title'])
    error = []

    try:
        if (Camera.query
                .filter(Camera.unique_id != form_camera.camera_id.data)
                .filter(Camera.name == form_camera.name.data).count()):
            flash("You must choose a unique name", "error")
            return redirect(url_for('routes_settings.settings_camera'))
        if 0 > form_camera.rotation.data > 360:
            flash("Rotation must be between 0 and 360 degrees", "error")
            return redirect(url_for('routes_settings.settings_camera'))

        mod_camera = Camera.query.filter(
            Camera.unique_id == form_camera.camera_id.data).first()
        mod_camera.name = form_camera.name.data

        if mod_camera.library == 'fswebcam':
            mod_camera.device = form_camera.device.data
            mod_camera.hflip = form_camera.hflip.data
            mod_camera.vflip = form_camera.vflip.data
            mod_camera.rotation = form_camera.rotation.data
            mod_camera.height = form_camera.height.data
            mod_camera.width = form_camera.width.data
            mod_camera.brightness = form_camera.brightness.data
            mod_camera.custom_options = form_camera.custom_options.data
        elif mod_camera.library == 'picamera':
            mod_camera.hflip = form_camera.hflip.data
            mod_camera.vflip = form_camera.vflip.data
            mod_camera.rotation = form_camera.rotation.data
            mod_camera.height = form_camera.height.data
            mod_camera.width = form_camera.width.data
            mod_camera.brightness = form_camera.brightness.data
            mod_camera.contrast = form_camera.contrast.data
            mod_camera.exposure = form_camera.exposure.data
            mod_camera.saturation = form_camera.saturation.data
            mod_camera.picamera_shutter_speed = form_camera.picamera_shutter_speed.data
            mod_camera.picamera_sharpness = form_camera.picamera_sharpness.data
            mod_camera.picamera_iso = int(form_camera.picamera_iso.data)
            mod_camera.picamera_awb = form_camera.picamera_awb.data
            mod_camera.picamera_awb_gain_red = form_camera.picamera_awb_gain_red.data
            mod_camera.picamera_awb_gain_blue = form_camera.picamera_awb_gain_blue.data
            mod_camera.picamera_exposure_mode = form_camera.picamera_exposure_mode.data
            mod_camera.picamera_meter_mode = form_camera.picamera_meter_mode.data
            mod_camera.picamera_image_effect = form_camera.picamera_image_effect.data
        else:
            error.append("Unknown camera library")

        if form_camera.output_id.data:
            mod_camera.output_id = form_camera.output_id.data
        else:
            mod_camera.output_id = None
        mod_camera.output_duration = form_camera.output_duration.data
        mod_camera.cmd_pre_camera = form_camera.cmd_pre_camera.data
        mod_camera.cmd_post_camera = form_camera.cmd_post_camera.data

        if not error:
            db.session.commit()
            control = DaemonControl()
            control.refresh_daemon_camera_settings()
    except Exception as except_msg:
        logger.exception(1)
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_camera'))


def camera_del(form_camera):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['delete']['title'],
        controller=TRANSLATIONS['camera']['title'])
    error = []

    camera = db_retrieve_table(
        Camera, unique_id=form_camera.camera_id.data)
    if camera.timelapse_started:
        error.append("Cannot delete camera if a time-lapse is currently "
                     "using it. Stop the time-lapse and try again.")

    if not error:
        try:
            delete_entry_with_id(
                Camera, form_camera.camera_id.data)
        except Exception as except_msg:
            error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_camera'))
