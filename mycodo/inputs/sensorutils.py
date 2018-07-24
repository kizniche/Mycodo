# coding=utf-8
#
#  sensorutils.py - commonly used functions for input devices (e.g. sensors)
#

import logging
import math

import os

from mycodo.utils.system_pi import all_conversions_daemon

logger = logging.getLogger("mycodo.sensor_utils")


def altitude(pressure_pa, sea_level_pa=101325.0):
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


def convert_units(measurement, unit, convert_to_unit, measure_value):
    """
    Convert from one unit to another, such as ppm to ppb.
    See UNIT_CONVERSIONS in config_devices_units.py for available conversions.

    :param measurement: measurement from MEASUREMENT_UNITS in config_devices_units.py
    :param unit: unit to convert from, from UNITS in config_devices_units.py
    :param convert_to_unit: string of "measurement,unit" of desired units to use (separated by ";")
    :param measure_value: The value to convert
    :return: converted value
    """
    measuement = measure_value
    conversions_dict = all_conversions_daemon()
    if convert_to_unit:
        for each_unit in convert_to_unit.split(';'):
            if each_unit.split(',')[0] == measurement:
                conversion = unit + '_to_' + each_unit.split(',')[1]
                if each_unit.split(',')[1] == unit:
                    return measuement
                elif conversion in conversions_dict:
                    replaced_str = conversions_dict[conversion].replace('x', str(measuement))
                    return float('{0:.5f}'.format(eval(replaced_str)))
    return measuement


def dewpoint(t, rh):
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


def is_device(path):
    """Determines if a path exists, created to check if a /dev/device exists"""
    try:
        os.stat("{dev}".format(dev=path))
    except OSError:
        return None
    return path
