# -*- coding: utf-8 -*-
#
#  config_translations.py - Mycodo phrases for translation
#

from flask_babel import lazy_gettext


TOOLTIPS_INPUT = {
    'period': {
        'title': lazy_gettext('Period'),
        'phrase': lazy_gettext('The duration (seconds) between input reads')},
    'convert_unit': {
        'title': None,
        'phrase': lazy_gettext('Select the unit of the measurement to be stored in the database')},
    'pre_output_id': {
        'title': lazy_gettext('Pre Output'),
        'phrase': lazy_gettext('Turn the selected output on before taking every measurement')},
    'pre_output_duration': {
        'title': lazy_gettext('Pre Out Duration'),
        'phrase': lazy_gettext('If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.')},
    'pre_output_during_measure': {
        'title': lazy_gettext('Pre During Measure'),
        'phrase': lazy_gettext('Check to turn the output off after (opposed to before) the measurement is complete')},
    'location': {
        'title': lazy_gettext('Location'),
        'phrase': lazy_gettext('The location to use for this device')},
    'i2c_location': {
        'title': lazy_gettext('I<sup>2</sup>C Address'),
        'phrase': lazy_gettext('The I2C address to access the device')},
    'uart_location': {
        'title': lazy_gettext('UART Device'),
        'phrase': lazy_gettext('The UART device location configured for this device')},
    'uart_baud_rate': {
        'title': lazy_gettext('Baud Rate'),
        'phrase': lazy_gettext('The UART baud rate')},
    'pin_cs': {
        'title': lazy_gettext('CS Pin'),
        'phrase': lazy_gettext('The GPIO (using BCM numbering) connected to the Cable Select pin')},
    'pin_miso': {
        'title': lazy_gettext('MISO Pin'),
        'phrase': lazy_gettext('The GPIO (using BCM numbering) connected to the MISO pin')},
    'pin_mosi': {
        'title': lazy_gettext('MOSI Pin'),
        'phrase': lazy_gettext('The GPIO (using BCM numbering) connected to the MOSI pin')},
    'pin_clock': {
        'title': lazy_gettext('Clock Pin'),
        'phrase': lazy_gettext('The GPIO (using BCM numbering) connected to the Clock pin')},
    'w1thermsensor_id': {
        'title': lazy_gettext('Device ID'),
        'phrase': lazy_gettext('Select the ID of the desired DS18B20 sensor')},
    'resolution': {
        'title': lazy_gettext('Resolution'),
        'phrase': lazy_gettext('Measurement resolution')},
    'thermocouple_type': {
        'title': lazy_gettext('Thermocouple'),
        'phrase': lazy_gettext('The type of thermocouple connected')},
    'ref_ohm': {
        'title': lazy_gettext('Reference Resistance'),
        'phrase': lazy_gettext('Reference resistance (Ohm)')},
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
    #     'phrase': lazy_gettext('')},
}
