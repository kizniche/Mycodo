# coding=utf-8
#
# From http://www.meteo-blog.net/2012-05/dewpoint-calculation-script-in-python/

import sys
import numpy as np
 
# approximation valid for
# 0 degC < T < 60 degC
# 1% < RH < 100%
# 0 degC < Td < 50 degC 
 
# constants
a = 17.271
b = 237.7 # degC
 
def dewpoint(temperature, humidity):
    dewpt = (b*gamma(temperature, humidity))/(a-gamma(temperature, humidity))
    return dewpt

def gamma(temperature, humidity):
    g = (a*temperature/(b+temperature))+np.log(humidity/100.0)
    return g
