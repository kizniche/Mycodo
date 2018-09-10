# -*- coding: utf-8 -*-
#
#  config_translations.py - Mycodo phrases for translation
#

from flask_babel import lazy_gettext


TOOLTIPS_INPUT = {
    'interface': {
        'title': lazy_gettext('Interface'),
        'phrase': lazy_gettext('The interface used to communicate')},
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
    'gpio_location': {
        'title': lazy_gettext('GPIO'),
        'phrase': lazy_gettext('The GPIO pin (BCM numbering) to access the device')},
    'i2c_location': {
        'title': lazy_gettext('I<sup>2</sup>C Address'),
        'phrase': lazy_gettext('The I2C address of the device')},
    'i2c_bus': {
        'title': lazy_gettext('I<sup>2</sup>C Bus'),
        'phrase': lazy_gettext('The I2C bus the device is connected to')},
    'uart_location': {
        'title': lazy_gettext('UART Device'),
        'phrase': lazy_gettext('The UART device location (e.g. /dev/ttyUSB1)')},
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
    'bt_location': {
        'title': lazy_gettext('MAC (XX:XX:XX:XX:XX:XX)'),
        'phrase': lazy_gettext('The MAC address of the input')},
    'bt_adapter': {
        'title': lazy_gettext('BT Adapter'),
        'phrase': lazy_gettext('The Bluetooth adapter of the input')},
    'w1thermsensor_id': {
        'title': lazy_gettext('Device ID'),
        'phrase': lazy_gettext('Select the ID of the desired DS18B20 sensor')},
    'resolution': {
        'title': lazy_gettext('Resolution'),
        'phrase': lazy_gettext('Measurement resolution')},
    'sensitivity': {
        'title': lazy_gettext('Sensitivity'),
        'phrase': lazy_gettext('Measurement sensitivity')},
    'thermocouple_type': {
        'title': lazy_gettext('RTD Probe Type'),
        'phrase': lazy_gettext('The type of thermocouple connected')},
    'ref_ohm': {
        'title': lazy_gettext('Reference Resistance'),
        'phrase': lazy_gettext('Reference resistance (Ohm)')},
    'cmd_command': {
        'title': lazy_gettext('Command'),
        'phrase': lazy_gettext('The command to executed (as user mycodo) to return a measurement value')},
    'measurement_units': {
        'title': lazy_gettext('Unit Measurement'),
        'phrase': lazy_gettext('Select a unit for the stored value')},
    'times_check': {
        'title': lazy_gettext('Times Check'),
        'phrase': lazy_gettext('Number of times to check')},
    'deadline': {
        'title': lazy_gettext('Deadline'),
        'phrase': lazy_gettext('Time (seconds) to wait until failure')},
    'port': {
        'title': lazy_gettext('Port'),
        'phrase': lazy_gettext('Host port number')},
    'weighting': {
        'title': lazy_gettext('Weighting'),
        'phrase': lazy_gettext('The weighting of the previous measurement on the current measurement. Range: 0.0 - 1.0. Used for smoothing measurements. 0.0 means no weighting.')},
    'sample_time': {
        'title': lazy_gettext('Sample Time'),
        'phrase': lazy_gettext('The amount of time (seconds) to sample the input before caluclating the measurement')},
    'rpm_pulses_per_rev': {
        'title': lazy_gettext('Pulses Per Rev'),
        'phrase': lazy_gettext('The number of pulses per revolution to calculate revolutions per minute (RPM)')},
    'adc_channel': {
        'title': lazy_gettext('Channel'),
        'phrase': lazy_gettext('The channel of the analog to digital converter.')},
    'adc_gain': {
        'title': lazy_gettext('Gain'),
        'phrase': lazy_gettext('Adjust the gain to change the measurable voltage range. See ADC documentation for details.')},
    'adc_resolution': {
        'title': lazy_gettext('Resolution'),
        'phrase': lazy_gettext('ADC Resolution (see ADC documentation)')},
    'adc_volts_min': {
        'title': lazy_gettext('Volts Min'),
        'phrase': lazy_gettext('Minimum analog to digital converter input voltage.')},
    'adc_volts_max': {
        'title': lazy_gettext('Volts Max'),
        'phrase': lazy_gettext('Maximum analog to digital converter input voltage.')},
    'adc_units_min': {
        'title': lazy_gettext('Units Min'),
        'phrase': lazy_gettext('Minimum unit to convert the voltage to.')},
    'adc_units_max': {
        'title': lazy_gettext('Units Max'),
        'phrase': lazy_gettext('Maximum unit to convert the voltage to.')},
    'adc_inverse_unit_scale': {
        'title': lazy_gettext('Inverse Unit Scale'),
        'phrase': lazy_gettext('Inverse the scale (example: a high measurement returns a low unit value)')},
    'sht_voltage': {
        'title': lazy_gettext('Voltage'),
        'phrase': lazy_gettext('The input voltage to the sensor')},
    # '': {
    #     'title': lazy_gettext(''),
    #     'phrase': lazy_gettext('')},
}
