# -*- coding: utf-8 -*-
import logging

from flask_babel import gettext

from mycodo.databases.models import CustomController
from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import Input
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.utils.utils_misc import determine_controller_type
from mycodo.utils.functions import parse_function_information
from mycodo.utils.inputs import parse_input_information

logger = logging.getLogger(__name__)


def measurement_mod_form(messages, page_refresh, form):
    mod_device = None
    device_info = None
    measurement_ids = []

    for key in form.keys():
        if (key.startswith("measurement_id_select_") and len(key) > 22 and
                key[22:] not in measurement_ids):
            measurement_ids.append(key[22:])
        if (key.startswith("measurement_id_config_") and len(key) > 22 and
                key[22:] not in measurement_ids):
            measurement_ids.append(key[22:])

    for each_meas_id in measurement_ids:
        try:
            mod_meas = DeviceMeasurements.query.filter(
                DeviceMeasurements.unique_id == each_meas_id).first()
            if not mod_meas:
                messages["error"].append("Count not find measurement")

            controller_type = determine_controller_type(mod_meas.device_id)

            if controller_type == "Input":
                mod_device = Input.query.filter(
                    Input.unique_id == mod_meas.device_id).first()
                device_info = parse_input_information()
            elif controller_type == "Function_Custom":
                mod_device = CustomController.query.filter(
                    CustomController.unique_id == mod_meas.device_id).first()
                device_info = parse_function_information()

            if not mod_device or not device_info:
                logger.error("Could not find mod_device or device_info")
                continue

            if mod_device.is_activated:
                messages["error"].append(
                    f"{gettext('Deactivate controller before modifying its settings')}: {mod_device.name}")
                break

            if ("measurement_id_{}".format(each_meas_id) in form and
                    form["measurement_id_{}".format(each_meas_id)] and
                    mod_meas.unique_id != form["measurement_id_{}".format(each_meas_id)]):
                test_meas_id = DeviceMeasurements.query.filter(
                    DeviceMeasurements.unique_id == form["measurement_id_{}".format(each_meas_id)]).first()
                if test_meas_id:
                    messages["error"].append(
                        f"Measurement ID must be unique. "
                        f"ID already exists: '{form['measurement_id_{}'.format(each_meas_id)]}'")
                elif not form["measurement_id_{}".format(each_meas_id)]:
                    messages["error"].append(f"Measurement ID is required")
                else:
                    mod_meas.unique_id = form["measurement_id_{}".format(each_meas_id)]

            if ("measurement_meas_name_{}".format(each_meas_id) in form and
                    form["measurement_meas_name_{}".format(each_meas_id)]):
                mod_meas.name = form["measurement_meas_name_{}".format(each_meas_id)]
            elif ("measurement_convert_name_{}".format(each_meas_id) in form and
                    form["measurement_convert_name_{}".format(each_meas_id)]):
                mod_meas.name = form["measurement_convert_name_{}".format(each_meas_id)]
            else:
                mod_meas.name = ''

            if ("measurement_meas_unit_{}".format(each_meas_id) in form and
                    ',' in form["measurement_meas_unit_{}".format(each_meas_id)]):
                measurement = form["measurement_meas_unit_{}".format(each_meas_id)].split(',')[0]
                unit = form["measurement_meas_unit_{}".format(each_meas_id)].split(',')[1]
                if (mod_meas.measurement != measurement or
                        mod_meas.unit != unit):
                    page_refresh = True
                mod_meas.measurement = measurement
                mod_meas.unit = unit

            if ('enable_channel_unit_select' in device_info[mod_device.device] and
                    device_info[mod_device.device]['enable_channel_unit_select'] and
                        ("measurement_meas_unit_{}".format(each_meas_id) not in form or
                         ',' not in form["measurement_meas_unit_{}".format(each_meas_id)])):
                if (mod_meas.measurement != '' or
                        mod_meas.unit != ''):
                    page_refresh = True
                mod_meas.measurement = ''
                mod_meas.unit = ''

            if "measurement_rescaled_meas_unit_{}".format(each_meas_id) in form:
                if (form["measurement_rescaled_meas_unit_{}".format(each_meas_id)] != '' and
                        ',' in form["measurement_rescaled_meas_unit_{}".format(each_meas_id)]):
                    rescaled_measurement = form["measurement_rescaled_meas_unit_{}".format(each_meas_id)].split(',')[0]
                    rescaled_unit = form["measurement_rescaled_meas_unit_{}".format(each_meas_id)].split(',')[1]
                    if (mod_meas.rescaled_measurement != rescaled_measurement or
                            mod_meas.rescaled_unit != rescaled_unit):
                        page_refresh = True
                    mod_meas.rescaled_measurement = rescaled_measurement
                    mod_meas.rescaled_unit = rescaled_unit
                elif form["measurement_rescaled_meas_unit_{}".format(each_meas_id)] == '':
                    if (mod_meas.rescaled_measurement != '' or
                            mod_meas.rescaled_unit != ''):
                        page_refresh = True
                    mod_meas.rescaled_measurement = ''
                    mod_meas.rescaled_unit = ''

            if "measurement_rescale_method_{}".format(each_meas_id) in form:
                mod_meas.rescale_method = form["measurement_rescale_method_{}".format(each_meas_id)]
            if "measurement_rescale_equation_{}".format(each_meas_id) in form:
                mod_meas.rescale_equation = form["measurement_rescale_equation_{}".format(each_meas_id)]
            if "measurement_scale_from_min_{}".format(each_meas_id) in form:
                mod_meas.scale_from_min = form["measurement_scale_from_min_{}".format(each_meas_id)]
            if "measurement_scale_from_max_{}".format(each_meas_id) in form:
                mod_meas.scale_from_max = form["measurement_scale_from_max_{}".format(each_meas_id)]
            if "measurement_scale_to_min_{}".format(each_meas_id) in form:
                mod_meas.scale_to_min = form["measurement_scale_to_min_{}".format(each_meas_id)]
            if "measurement_scale_to_max_{}".format(each_meas_id) in form:
                mod_meas.scale_to_max = form["measurement_scale_to_max_{}".format(each_meas_id)]
            if "measurement_invert_scale_{}".format(each_meas_id) in form:
                mod_meas.invert_scale = True
            else:
                mod_meas.invert_scale = False
            if "measurement_conversion_id_{}".format(each_meas_id) in form:
                mod_meas.conversion_id = form["measurement_conversion_id_{}".format(each_meas_id)]

            if not messages["error"]:
                db.session.commit()

        except Exception as except_msg:
            logger.exception(1)
            messages["error"].append(str(except_msg))

    return messages, page_refresh
