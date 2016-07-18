# coding=utf-8
#
# From http://www.meteo-blog.net/2012-05/dewpoint-calculation-script-in-python/

import sys
import numpy as np


def dewpoint(temperature, humidity):
    # approximation valid for
    # 0 degC < T < 60 degC
    # 1% < RH < 100%
    # 0 degC < Td < 50 degC 
    a = 17.271
    b = 237.7 # degC
    dewpt = (b*gamma(temperature, humidity, a, b))/(a-gamma(temperature, humidity, a, b))
    return dewpt

def gamma(temperature, humidity, a, b):
    g = (a*temperature/(b+temperature))+np.log(humidity/100.0)
    return g
