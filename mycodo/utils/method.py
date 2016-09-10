# coding=utf-8

import datetime
from math import sin, radians


def sine_wave_y_out(amplitude, frequency, shift_angle, shift_y, angle_in=None):
    if angle_in is None:
        now = datetime.datetime.now()
        dt = datetime.timedelta(hours=now.hour, minutes=now.minute, seconds=now.second)
        secs_per_day = 24*60*60
        angle = dt.total_seconds()/secs_per_day*360
    else:
        angle = angle_in

    return (amplitude*sin(radians(frequency*(angle-shift_angle))))+shift_y

print(sine_wave_y_out(5.0, 5.0, 200.0, 33.0))
