# coding=utf-8
#
# From https://github.com/mk-fg/sht-sensor

import logging
import math

import os

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
