# -*- coding: utf-8 -*-
import logging

import sqlalchemy
from flask import flash
from flask import url_for
from flask_babel import gettext

from mycodo.config import MATH_INFO
from mycodo.databases.models import Conversion
from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import DisplayOrder
from mycodo.databases.models import Input
from mycodo.databases.models import Math
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.utils.utils_general import add_display_order
from mycodo.mycodo_flask.utils.utils_general import controller_activate_deactivate
from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.mycodo_flask.utils.utils_general import flash_form_errors
from mycodo.mycodo_flask.utils.utils_general import flash_success_errors
from mycodo.mycodo_flask.utils.utils_general import reorder
from mycodo.mycodo_flask.utils.utils_general import return_dependencies
from mycodo.utils.system_pi import csv_to_list_of_str
from mycodo.utils.system_pi import get_measurement
from mycodo.utils.system_pi import list_to_csv
from mycodo.utils.system_pi import return_measurement_info

logger = logging.getLogger(__name__)


#
# Math manipulation
#

def math_add(form_add_math):
    action = '{action} {controller}'.format(
        action=gettext("Add"),
        controller=gettext("Math"))
    error = []

    dep_unmet, _ = return_dependencies(form_add_math.math_type.data)
    if dep_unmet:
        list_unmet_deps = []
        for each_dep in dep_unmet:
            list_unmet_deps.append(each_dep[0])
        error.append("The {dev} device you're trying to add has unmet dependencies: {dep}".format(
            dev=form_add_math.math_type.data, dep=', '.join(list_unmet_deps)))

    if form_add_math.validate():
        new_math = Math()
        new_math.name = str(MATH_INFO[form_add_math.math_type.data]['name'])
        new_math.math_type = form_add_math.math_type.data

        try:
            new_math.save()

            display_order = csv_to_list_of_str(
                DisplayOrder.query.first().math)
            DisplayOrder.query.first().math = add_display_order(
                display_order, new_math.unique_id)
            db.session.commit()

            if not MATH_INFO[form_add_math.math_type.data]['measure']:
                new_measurement = DeviceMeasurements()
                new_measurement.device_id = new_math.unique_id
                new_measurement.channel = 0
                new_measurement.save()
            else:
                for each_channel, measure_info in MATH_INFO[form_add_math.math_type.data]['measure'].items():
                    new_measurement = DeviceMeasurements()
                    if 'name' in measure_info and measure_info['name']:
                        new_measurement.name = measure_info['name']
                    new_measurement.device_id = new_math.unique_id
                    new_measurement.measurement = measure_info['measurement']
                    new_measurement.unit = measure_info['unit']
                    new_measurement.channel = each_channel
                    new_measurement.save()

            flash(gettext(
                "%(type)s Math with ID %(id)s (%(uuid)s) successfully added",
                type=form_add_math.math_type.data,
                id=new_math.id,
                uuid=new_math.unique_id),
                  "success")
        except sqlalchemy.exc.OperationalError as except_msg:
            error.append(except_msg)
        except sqlalchemy.exc.IntegrityError as except_msg:
            error.append(except_msg)
        flash_success_errors(error, action, url_for('routes_page.page_data'))
    else:
        flash_form_errors(form_add_math)

    if dep_unmet:
        return 1


def math_mod(form_mod_math, form_mod_type=None):
    action = '{action} {controller}'.format(
        action=gettext("Modify"),
        controller=gettext("Math"))
    error = []

    try:
        mod_math = Math.query.filter(
            Math.unique_id == form_mod_math.math_id.data).first()

        if mod_math.is_activated:
            error.append(gettext(
                "Deactivate Math controller before modifying its "
                "settings"))

        if form_mod_type and not form_mod_type.validate():
            error.append(gettext("Error in form field(s)"))
            flash_form_errors(form_mod_type)

        mod_math.name = form_mod_math.name.data
        mod_math.period = form_mod_math.period.data
        mod_math.max_measure_age = form_mod_math.max_measure_age.data
        mod_math.start_offset = form_mod_math.start_offset.data

        measurements = DeviceMeasurements.query.filter(
            DeviceMeasurements.device_id == form_mod_math.math_id.data).all()

        # Set each measurement to the same measurement/unit
        if form_mod_math.select_measurement_unit.data:
            for each_measurement in measurements:
                if ',' in form_mod_math.select_measurement_unit.data:
                    each_measurement.measurement = form_mod_math.select_measurement_unit.data.split(',')[0]
                    each_measurement.unit = form_mod_math.select_measurement_unit.data.split(',')[1]
                else:
                    each_measurement.measurement = ''
                    each_measurement.unit = ''

        # Enable/disable Channels
        if form_mod_math.measurements_enabled.data:
            for each_measurement in measurements:
                if each_measurement.unique_id in form_mod_math.measurements_enabled.data:
                    each_measurement.is_enabled = True
                else:
                    each_measurement.is_enabled = False

        # Collect inputs and measurement name and units
        if mod_math.math_type in ['average',
                                  'difference',
                                  'statistics',
                                  'verification']:
            if len(form_mod_math.inputs.data) < 2:
                error.append("At least two Inputs must be selected")
            if form_mod_math.inputs.data:
                inputs_joined = ";".join(form_mod_math.inputs.data)
                mod_math.inputs = inputs_joined
            else:
                mod_math.inputs = ''

        if mod_math.math_type == 'average_single':
            mod_math.inputs = form_mod_type.average_input.data

            # Change measurement information
            if form_mod_type.average_input.data and ',' in form_mod_type.average_input.data:
                measurement_id = form_mod_type.average_input.data.split(',')[1]
                selected_measurement = get_measurement(measurement_id)
                if selected_measurement:
                    conversion = Conversion.query.filter(
                        Conversion.unique_id == selected_measurement.conversion_id).first()
                else:
                    conversion = None
                channel, unit, measurement = return_measurement_info(
                    selected_measurement, conversion)

                mod_measurement = DeviceMeasurements.query.filter(
                    DeviceMeasurements.device_id == form_mod_math.math_id.data).first()
                mod_measurement.measurement = measurement
                mod_measurement.unit = unit

        if mod_math.math_type == 'difference':
            if len(form_mod_math.inputs.data) != 2:
                error.append("Only two Inputs must be selected")
            mod_math.difference_reverse_order = form_mod_type.difference_reverse_order.data
            mod_math.difference_absolute = form_mod_type.difference_absolute.data

        if mod_math.math_type == 'equation':
            mod_math.equation_input = form_mod_type.equation_input.data
            mod_math.equation = form_mod_type.equation.data

        elif mod_math.math_type == 'humidity':
            mod_math.dry_bulb_t_id = form_mod_type.dry_bulb_temperature.data.split(',')[0]
            mod_math.dry_bulb_t_measure_id = form_mod_type.dry_bulb_temperature.data.split(',')[1]
            dbt_input = Input.query.filter(
                Input.unique_id == mod_math.dry_bulb_t_id).first()
            dbt_math = Input.query.filter(
                Math.unique_id == mod_math.dry_bulb_t_id).first()
            if not dbt_input and not dbt_math:
                error.append("Invalid dry-bulb temperature selection: Must be a valid Input or Math")

            mod_math.wet_bulb_t_id = form_mod_type.wet_bulb_temperature.data.split(',')[0]
            mod_math.wet_bulb_t_measure_id = form_mod_type.wet_bulb_temperature.data.split(',')[1]
            wbt_input = Input.query.filter(
                Input.unique_id == mod_math.wet_bulb_t_id).first()
            wbt_math = Input.query.filter(
                Math.unique_id == mod_math.wet_bulb_t_id).first()
            if not wbt_input and not wbt_math:
                error.append("Invalid wet-bulb temperature selection: Must be a valid Input or Math")

            if form_mod_type.pressure.data:
                mod_math.pressure_pa_id = form_mod_type.pressure.data.split(',')[0]
                mod_math.pressure_pa_measure_id = form_mod_type.pressure.data.split(',')[1]
            else:
                mod_math.pressure_pa_id = None
                mod_math.pressure_pa_measure_id = None

        elif mod_math.math_type == 'verification':
            mod_math.max_difference = form_mod_type.max_difference.data

        elif mod_math.math_type == 'vapor_pressure_deficit':
            mod_math.unique_id_1 = form_mod_type.unique_id_1.data.split(',')[0]
            mod_math.unique_measurement_id_1 = form_mod_type.unique_id_1.data.split(',')[1]
            vpd_input = Input.query.filter(
                Input.unique_id == mod_math.unique_id_1).first()
            vpd_math = Input.query.filter(
                Math.unique_id == mod_math.unique_id_1).first()
            if not vpd_input and not vpd_math:
                error.append("Invalid vapor pressure deficit temperature selection: Must be a valid Input or Math")

            mod_math.unique_id_2 = form_mod_type.unique_id_2.data.split(',')[0]
            mod_math.unique_measurement_id_2 = form_mod_type.unique_id_2.data.split(',')[1]
            vpd_input = Input.query.filter(
                Input.unique_id == mod_math.unique_id_2).first()
            vpd_math = Input.query.filter(
                Math.unique_id == mod_math.unique_id_2).first()
            if not vpd_input and not vpd_math:
                error.append("Invalid vapor pressure deficit humidity selection: Must be a valid Input or Math")

        if not error:
            db.session.commit()
    except Exception as except_msg:
        logger.exception(1)
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_data'))


def math_measurement_mod(form):
    action = '{action} {controller}'.format(
        action=gettext("Modify"),
        controller=gettext("Measurement"))
    error = []

    try:
        mod_meas = DeviceMeasurements.query.filter(
            DeviceMeasurements.unique_id == form.math_measurement_id.data).first()

        mod_math = Math.query.filter(Math.unique_id == mod_meas.device_id).first()
        if mod_math.is_activated:
            error.append(gettext(
                "Deactivate controller before modifying its settings"))

        mod_meas.name = form.name.data

        if form.select_measurement_unit.data:
            if ',' in form.select_measurement_unit.data:
                mod_meas.measurement = form.select_measurement_unit.data.split(',')[0]
                mod_meas.unit = form.select_measurement_unit.data.split(',')[1]
            else:
                mod_meas.measurement = ''
                mod_meas.unit = ''

        if form.convert_to_measurement_unit.data:
            mod_meas.conversion_id = form.convert_to_measurement_unit.data

        if not error:
            db.session.commit()

    except Exception as except_msg:
        logger.exception(1)
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_data'))


def math_del(form_mod_math):
    action = '{action} {controller}'.format(
        action=gettext("Delete"),
        controller=gettext("Math"))
    error = []

    math_id = form_mod_math.math_id.data

    try:
        math = Math.query.filter(
            Math.unique_id == math_id).first()
        if math.is_activated:
            controller_activate_deactivate(
                'deactivate',
                'Math',
                form_mod_math.math_id.data)

        device_measurements = DeviceMeasurements.query.filter(
            DeviceMeasurements.device_id == math_id).all()

        for each_measurement in device_measurements:
            delete_entry_with_id(DeviceMeasurements, each_measurement.unique_id)

        delete_entry_with_id(Math, math_id)
        try:
            display_order = csv_to_list_of_str(DisplayOrder.query.first().math)
            display_order.remove(math_id)
            DisplayOrder.query.first().math = list_to_csv(display_order)
        except Exception:  # id not in list
            pass
        db.session.commit()
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_data'))


def math_reorder(math_id, display_order, direction):
    action = '{action} {controller}'.format(
        action=gettext("Reorder"),
        controller=gettext("Math"))
    error = []
    try:
        status, reord_list = reorder(display_order,
                                     math_id,
                                     direction)
        if status == 'success':
            DisplayOrder.query.first().math = ','.join(map(str, reord_list))
            db.session.commit()
        elif status == 'error':
            error.append(reord_list)
    except Exception as except_msg:
        error.append(except_msg)
    flash_success_errors(error, action, url_for('routes_page.page_data'))


def math_activate(form_mod_math):
    controller_activate_deactivate('activate',
                                   'Math',
                                   form_mod_math.math_id.data)


def math_deactivate(form_mod_math):
    controller_activate_deactivate('deactivate',
                                   'Math',
                                   form_mod_math.math_id.data)
