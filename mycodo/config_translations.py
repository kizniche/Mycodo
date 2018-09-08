# -*- coding: utf-8 -*-
#
#  config_translations.py - Mycodo phrases for translation
#

from flask_babel import lazy_gettext


TOOLTIPS_INPUT = {
    'period': lazy_gettext('The duration (seconds) between input reads'),
    'pre_output_id': lazy_gettext('Turn the selected output on before taking every measurement'),
    'pre_output_duration': lazy_gettext('If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.'),
    'pre_output_during_measure': lazy_gettext('Check to turn the output off after (opposed to before) the measurement is complete'),
    'i2c_location': lazy_gettext('The I2C address to access the device'),
    # '': lazy_gettext(''),
}
