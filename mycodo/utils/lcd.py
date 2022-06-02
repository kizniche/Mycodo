# -*- coding: utf-8 -*-
#
#  lcd.py - Mycodo core utils
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
import logging

from mycodo.databases.models import Conversion
from mycodo.databases.models import Function
from mycodo.databases.models import Input
from mycodo.databases.models import Output
from mycodo.databases.models import PID
from mycodo.databases.models import Unit
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.logging_utils import set_log_level
from mycodo.utils.system_pi import add_custom_units
from mycodo.utils.system_pi import get_measurement
from mycodo.utils.system_pi import return_measurement_info

logger = logging.getLogger("mycodo.utils.lcd")
logger.setLevel(set_log_level(logging))


def format_measurement_line(device_id, measure_id, val_rounded, lcd_x_characters, display_unit=True, label=None):
    unit_display, unit_length, name = get_measurement_info(device_id, measure_id)

    if unit_length:
        value_length = len(str(val_rounded))
        name_length = lcd_x_characters - value_length - unit_length - 2
        if label:
            name_cropped = label.ljust(name_length)[:name_length]
        else:
            name_cropped = name.ljust(name_length)[:name_length]
        if display_unit:
            line_display = '{name} {value} {unit}'.format(
                name=name_cropped,
                value=val_rounded,
                unit=unit_display.replace('°', u''))
        else:
            line_display = '{name} {value}'.format(
                name=name_cropped,
                value=val_rounded)
    else:
        value_length = len(str(val_rounded))
        name_length = lcd_x_characters - value_length - 1
        name_cropped = name[:name_length]
        if name_cropped:
            line_str = '{name} {value}'.format(
                name=name_cropped,
                value=val_rounded)
        else:
            line_str = val_rounded
        line_display = line_str

    return line_display

def get_measurement_info(device_id, measurement_id):
    unit_display = ""
    name = ""

    device_measurement = get_measurement(measurement_id)
    conversion = db_retrieve_table_daemon(
        Conversion, unique_id=device_measurement.conversion_id)
    channel, unit, measurement = return_measurement_info(
        device_measurement, conversion)

    dict_units = add_custom_units(
        db_retrieve_table_daemon(Unit, entry='all'))
    if unit in dict_units:
        unit_display = dict_units[unit]['unit']
    if unit_display:
        unit_length = len(unit_display.replace('°', u''))
    else:
        unit_length = 0

    controllers = [
        Output,
        PID,
        Input,
        Function
    ]
    for each_controller in controllers:
        controller_found = db_retrieve_table_daemon(
            each_controller, unique_id=device_id)
        if controller_found:
            name = controller_found.name
            break

    return unit_display, unit_length, name
