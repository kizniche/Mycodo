# -*- coding: utf-8 -*-
import logging

from flask_babel import gettext

from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import CustomController
from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import Input
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.utils.utils_general import flash_success_errors
from mycodo.mycodo_flask.utils.utils_misc import determine_controller_type
from mycodo.utils.functions import parse_function_information
from mycodo.utils.inputs import parse_input_information

logger = logging.getLogger(__name__)


def measurement_mod(form, return_url):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['modify']['title'],
        controller=TRANSLATIONS['measurement']['title'])
    error = []

    mod_device = None
    device_info = None

    try:
        mod_meas = DeviceMeasurements.query.filter(
            DeviceMeasurements.unique_id == form.measurement_id.data).first()

        controller_type = determine_controller_type(mod_meas.device_id)

        if controller_type == "Input":
            mod_device = Input.query.filter(Input.unique_id == mod_meas.device_id).first()
            device_info = parse_input_information()
        elif controller_type == "Function":
            mod_device = CustomController.query.filter(CustomController.unique_id == mod_meas.device_id).first()
            device_info = parse_function_information()

        if not mod_device or not device_info:
            logger.error("Could not find mod_device or device_info")
            return

        if mod_device.is_activated:
            error.append(gettext(
                "Deactivate controller before modifying its settings"))

        mod_meas.name = form.name.data

        if form.device_type.data == 'measurement_select':
            if not form.select_measurement_unit.data:
                error.append("Must select a measurement unit")
            else:
                mod_meas.measurement = form.select_measurement_unit.data.split(',')[0]
                mod_meas.unit = form.select_measurement_unit.data.split(',')[1]

        elif form.device_type.data == 'measurement_convert':
            if ('enable_channel_unit_select' in device_info[mod_device.device] and
                    device_info[mod_device.device]['enable_channel_unit_select']):
                if ',' in form.select_measurement_unit.data:
                    mod_meas.measurement = form.select_measurement_unit.data.split(',')[0]
                    mod_meas.unit = form.select_measurement_unit.data.split(',')[1]
                else:
                    mod_meas.measurement = ''
                    mod_meas.unit = ''

            if form.rescaled_measurement_unit.data != '' and ',' in form.rescaled_measurement_unit.data:
                mod_meas.rescaled_measurement = form.rescaled_measurement_unit.data.split(',')[0]
                mod_meas.rescaled_unit = form.rescaled_measurement_unit.data.split(',')[1]
            elif form.rescaled_measurement_unit.data == '':
                mod_meas.rescaled_measurement = ''
                mod_meas.rescaled_unit = ''

            mod_meas.scale_from_min = form.scale_from_min.data
            mod_meas.scale_from_max = form.scale_from_max.data
            mod_meas.scale_to_min = form.scale_to_min.data
            mod_meas.scale_to_max = form.scale_to_max.data
            mod_meas.invert_scale = form.invert_scale.data
            mod_meas.conversion_id = form.convert_to_measurement_unit.data

        if not error:
            db.session.commit()

    except Exception as except_msg:
        logger.exception(1)
        error.append(except_msg)

    flash_success_errors(error, action, return_url)
