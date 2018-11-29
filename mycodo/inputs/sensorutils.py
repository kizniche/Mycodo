# coding=utf-8
#
#  sensorutils.py - commonly used functions for input devices (e.g. sensors)
#

import logging
import math

import os

from mycodo.databases.models import Conversion
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.system_pi import all_conversions

logger = logging.getLogger("mycodo.sensor_utils")


def calculate_altitude(pressure_pa, sea_level_pa=101325.0):
    """
    Calculates the altitude (m) from pressure (Pa)
    :param pressure_pa: Measured pressure (Pa)
    :param sea_level_pa: Pressure (Pa) at sea level
    :return: altitude in meters
    """
    if pressure_pa < 0:
        logger.error("Erroneous Pressure to calculate altitude: "
                     "{press} Pa".format(press=pressure_pa))
        return None
    alt_meters = 44330.0 * (1.0 - pow(pressure_pa / sea_level_pa, (1.0 / 5.255)))
    return float("{:.3f}".format(alt_meters))


def convert_units(conversion_id, measure_value):
    """
    Convert from one unit to another, such as ppm to ppb.
    See UNIT_CONVERSIONS in config_devices_units.py for available conversions.

    :param conversion_id: conversion ID
    :param measure_value: The value to convert
    :return: converted value
    """
    conversion = db_retrieve_table_daemon(Conversion, unique_id=conversion_id)
    replaced_str = conversion.equation.replace('x', str(measure_value))
    return float('{0:.5f}'.format(eval(replaced_str)))


def calculate_dewpoint(t, rh):
    """Calculate dewpoint from temperature and relative humidity"""
    dict_tn = dict(water=243.12, ice=272.62)
    dict_m = dict(water=17.62, ice=22.46)
    if t >= 0:
        t_range = 'water'
    else:
        t_range = 'ice'
    tn, m = dict_tn[t_range], dict_m[t_range]
    if rh / 100.0 <= 0:
        # Cannot perform log on 0 or negative number
        return 0.0
    else:
        return float(
            tn * (math.log(rh / 100.0) + (m * t) / (tn + t))
            / (m - math.log(rh / 100.0) - m * t / (tn + t)))


def calculate_saturated_vapor_pressure(temperature):
    return 610.7 * 10 ** (7.5 * temperature / (237.3 + temperature))


def calculate_vapor_pressure_deficit(temperature, relative_humidity):
    svp = calculate_saturated_vapor_pressure(temperature)
    return ((100 - relative_humidity) / 100) * svp


def is_device(path):
    """Determines if a path exists, created to check if a /dev/device exists"""
    try:
        os.stat("{dev}".format(dev=path))
    except OSError:
        return None
    return path
