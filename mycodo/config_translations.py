# -*- coding: utf-8 -*-
#
#  config_translations.py - Mycodo phrases for translation
#

from flask_babel import lazy_gettext


TOOLTIPS_INPUT = {
    'period': {
        'title': lazy_gettext('Period'),
        'phrase': lazy_gettext('The duration (seconds) between input reads')},
    'pre_output_id': {
        'title': lazy_gettext('Pre Output'),
        'phrase': lazy_gettext('Turn the selected output on before taking every measurement')},
    'pre_output_duration': {
        'title': lazy_gettext('Pre Out Duration'),
        'phrase': lazy_gettext('If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.')},
    'pre_output_during_measure': {
        'title': lazy_gettext('Pre During Measure'),
        'phrase': lazy_gettext('Check to turn the output off after (opposed to before) the measurement is complete')},
    'i2c_location': {
        'title': lazy_gettext('I<sup>2</sup>C Address'),
        'phrase': lazy_gettext('The I2C address to access the device')},
    'convert_unit': {
        'title': None,
        'phrase': lazy_gettext('Select the unit of the measurement to be stored in the database')},
    'location': {
        'title': lazy_gettext('Location'),
        'phrase': lazy_gettext('The location to use for this device')},
    # '': {
    #     'title': lazy_gettext(''),
    #     'phrase': lazy_gettext('')},
    # '': {
    #     'title': lazy_gettext(''),
    #     'phrase': lazy_gettext('')},
    # '': {
    #     'title': lazy_gettext(''),
    #     'phrase': lazy_gettext('')},
    # '': {
    #     'title': lazy_gettext(''),
    #     'phrase': lazy_gettext('')},
    # '': {
    #     'title': lazy_gettext(''),
    #     'phrase': lazy_gettext('')
    # },
}
