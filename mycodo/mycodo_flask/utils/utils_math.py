# -*- coding: utf-8 -*-
import logging

import sqlalchemy
from flask import flash
from flask import url_for
from flask_babel import gettext

from mycodo.config import MATH_INFO
from mycodo.config_devices_units import MEASUREMENTS
from mycodo.databases.models import DisplayOrder
from mycodo.databases.models import Input
from mycodo.databases.models import Math
from mycodo.databases.models import MathMeasurements
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.utils.utils_general import add_display_order
from mycodo.mycodo_flask.utils.utils_general import controller_activate_deactivate
from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.mycodo_flask.utils.utils_general import flash_form_errors
from mycodo.mycodo_flask.utils.utils_general import flash_success_errors
from mycodo.mycodo_flask.utils.utils_general import reorder
from mycodo.mycodo_flask.utils.utils_general import return_dependencies
from mycodo.utils.system_pi import csv_to_list_of_str
from mycodo.utils.system_pi import list_to_csv

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
        new_math.name = ''
        new_math.math_type = form_add_math.math_type.data

        if form_add_math.math_type.data in MATH_INFO:
            new_math.name += '{name}'.format(name=MATH_INFO[form_add_math.math_type.data]['name'])

        try:
            new_math.save()

            display_order = csv_to_list_of_str(
                DisplayOrder.query.first().math)
            DisplayOrder.query.first().math = add_display_order(
                display_order, new_math.unique_id)
            db.session.commit()

            if not MATH_INFO[form_add_math.math_type.data]['measure']:
                new_measurement = MathMeasurements()
                new_measurement.save()
            else:
                for each_measurement, unit_info in MATH_INFO[form_add_math.math_type.data]['measure'].items():
                    for each_unit, channel_data in unit_info.items():
                        for each_channel in channel_data.keys():
                            new_measurement = MathMeasurements()
                            new_measurement.math_id = new_math.unique_id
                            new_measurement.measurement = each_measurement
                            new_measurement.unit = each_unit
                            new_measurement.channel = each_channel
                            if len(channel_data) == 1:
                                new_measurement.single_channel = True
                            else:
                                new_measurement.single_channel = False
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

    if not form_mod_math.validate():
        error.append(gettext("Error in form field(s)"))
        flash_form_errors(form_mod_math)

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

        # Collect inputs and measurement name and units
        if mod_math.math_type in ['average',
                                  'difference',
                                  'median',
                                  'maximum',
                                  'minimum',
                                  'verification']:
            if len(form_mod_math.inputs.data) < 2:
                error.append("At least two Inputs must be selected")
            if form_mod_math.inputs.data:
                inputs_joined = ";".join(form_mod_math.inputs.data)
                mod_math.inputs = inputs_joined
            else:
                mod_math.inputs = ''

        # Set measurement and units
        if mod_math.math_type in ['average',
                                  'average_single',
                                  'difference',
                                  'equation',
                                  'median',
                                  'maximum',
                                  'minimum',
                                  'verification']:
            mod_math.measure = form_mod_math.selected_measurement_unit.data.split(',')[0]
            mod_math.measure_units = form_mod_math.selected_measurement_unit.data

        if mod_math.math_type == 'average_single':
            mod_math.inputs = form_mod_type.average_input.data

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
            mod_math.dry_bulb_t_measure = form_mod_type.dry_bulb_temperature.data.split(',')[1]
            dbt_input = Input.query.filter(
                Input.unique_id == mod_math.dry_bulb_t_id).first()
            dbt_math = Input.query.filter(
                Math.unique_id == mod_math.dry_bulb_t_id).first()
            if not dbt_input and not dbt_math:
                error.append("Invalid dry-bulb temperature selection: Must be a valid Input or Math")
            if 'temperature' not in mod_math.dry_bulb_t_measure:
                error.append("Invalid dry-bulb temperature selection: Must be a temperature measurement")

            mod_math.wet_bulb_t_id = form_mod_type.wet_bulb_temperature.data.split(',')[0]
            mod_math.wet_bulb_t_measure = form_mod_type.wet_bulb_temperature.data.split(',')[1]
            wbt_input = Input.query.filter(
                Input.unique_id == mod_math.wet_bulb_t_id).first()
            wbt_math = Input.query.filter(
                Math.unique_id == mod_math.wet_bulb_t_id).first()
            if not wbt_input and not wbt_math:
                error.append("Invalid wet-bulb temperature selection: Must be a valid Input or Math")
            if 'temperature' not in mod_math.wet_bulb_t_measure:
                error.append("Invalid wet-bulb temperature selection: Must be a temperature measurement")

            if form_mod_type.pressure.data:
                mod_math.pressure_pa_id = form_mod_type.pressure.data.split(',')[0]
                pressure_input = Input.query.filter(
                    Input.unique_id == mod_math.pressure_pa_id).first()
                if not pressure_input or 'pressure' not in pressure_input.measurements:
                    error.append("Invalid pressure selection")
                mod_math.pressure_pa_measure = form_mod_type.pressure.data.split(',')[1]
            else:
                mod_math.pressure_pa_id = None
                mod_math.pressure_pa_measure = None

        elif mod_math.math_type == 'verification':
            mod_math.max_difference = form_mod_type.max_difference.data

        if not error:
            db.session.commit()
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_data'))


def math_del(form_mod_math):
    action = '{action} {controller}'.format(
        action=gettext("Delete"),
        controller=gettext("Math"))
    error = []

    try:
        math = Math.query.filter(
            Math.unique_id == form_mod_math.math_id.data).first()
        if math.is_activated:
            controller_activate_deactivate(
                'deactivate',
                'Math',
                form_mod_math.math_id.data)

        delete_entry_with_id(Math, form_mod_math.math_id.data)
        try:
            display_order = csv_to_list_of_str(DisplayOrder.query.first().math)
            display_order.remove(form_mod_math.math_id.data)
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
