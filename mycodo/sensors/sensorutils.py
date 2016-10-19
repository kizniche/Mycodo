# coding=utf-8
#
# From https://github.com/mk-fg/sht-sensor

import math

def dewpoint(t, rh):
    dict_tn = dict(water=243.12, ice=272.62)
    dict_m = dict(water=17.62, ice=22.46)
    if t is None:
        t, rh = self.read_t(), None
    if rh is None:
        rh = self.read_rh(t)
    if t >= 0:
        t_range = 'water'
    else:
        t_range = 'ice'
    tn, m = dict_tn[t_range], dict_m[t_range]
    if rh/100.0 <= 0:
        # Cannot perform log on 0 or negative number
        return 0.0
    else:
        return float(
            tn * (math.log(rh / 100.0) + (m * t) / (tn + t))
            / (m - math.log(rh / 100.0) - m * t / (tn + t)) )


def altitude(pressure_pa, sealevel_pa=101325.0):
    """Calculates the altitude in meters."""
    altitude = 44330.0 * (1.0 - pow(pressure_pa / sealevel_pa, (1.0/5.255)))
    return altitude


def c_to_f(temperture_c):
    return 9.0/5.0 * temperture_c + 32
