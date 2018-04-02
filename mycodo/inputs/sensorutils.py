# coding=utf-8
#
# From https://github.com/mk-fg/sht-sensor

import logging
import math

import os

from mycodo.config import UNIT_CONVERSIONS

logger = logging.getLogger("mycodo.sensor_utils")


def altitude(pressure_pa, sea_level_pa=101325.0):
    """Calculates the altitude in meters."""
    if pressure_pa < 0:
        logger.error("Erroneous Pressure to calculate altitude: "
                     "{press} Pa".format(press=pressure_pa))
        return None
    alt = 44330.0 * (1.0 - pow(pressure_pa / sea_level_pa, (1.0 / 5.255)))
    return alt


def c_to_f(temp_c):
    return 9.0 / 5.0 * temp_c + 32

def convert_units(measurement, unit, convert_to_unit, measure_value):
    measuement = measure_value
    if convert_to_unit:
        for each_unit in convert_to_unit.split(';'):
            if each_unit.split(',')[0] == measurement:
                conversion = unit + '_to_' + each_unit.split(',')[1]
                if each_unit.split(',')[1] == unit:
                    return measuement
                elif conversion in UNIT_CONVERSIONS:
                    replaced_str = UNIT_CONVERSIONS[conversion].replace('x', str(measuement))
                    return float('{0:.5f}'.format(eval(replaced_str)))
    return measuement


def dewpoint(t, rh):
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
    try:
        os.stat("{dev}".format(dev=path))
    except OSError:
        return None
    return path
