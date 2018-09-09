# -*- coding: utf-8 -*-
#
# forms_input.py - Input Flask Forms
#
import logging

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import DecimalField
from wtforms import IntegerField
from wtforms import SelectField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import validators
from wtforms import widgets
from wtforms.validators import DataRequired

from mycodo.config_translations import TOOLTIPS_INPUT
from mycodo.utils.inputs import parse_input_information

logger = logging.getLogger("mycodo.forms_input")


class InputAdd(FlaskForm):
    choices_inputs = [('', lazy_gettext('Select Input to Add'))]

    dict_inputs = parse_input_information()

    # Sort dictionary entries by input_manufacturer, then common_name_input
    # Results in list of sorted dictionary keys
    list_tuples_sorted = sorted(dict_inputs.items(), key=lambda x: (x[1]['input_manufacturer'], x[1]['common_name_input']))
    list_inputs_sorted = []
    for each_input in list_tuples_sorted:
        list_inputs_sorted.append(each_input[0])

    for each_input in list_inputs_sorted:
        if 'interfaces' not in dict_inputs[each_input]:
            choices_inputs.append(
                ('{inp},'.format(inp=each_input),
                 '{manuf}: {name}: {meas}'.format(
                     manuf=dict_inputs[each_input]['input_manufacturer'],
                     name=dict_inputs[each_input]['common_name_input'],
                     meas=dict_inputs[each_input]['common_name_measurements'])))
        else:
            for each_interface in dict_inputs[each_input]['interfaces']:
                choices_inputs.append(
                    ('{inp},{int}'.format(inp=each_input, int=each_interface),
                     '{manuf}: {name}: {meas} ({int})'.format(
                        manuf=dict_inputs[each_input]['input_manufacturer'],
                        name=dict_inputs[each_input]['common_name_input'],
                        meas=dict_inputs[each_input]['common_name_measurements'],
                        int=each_interface)))

    input_type = SelectField(
        choices=choices_inputs,
        validators=[DataRequired()]
    )
    input_add = SubmitField(lazy_gettext('Add Input'))


class InputMod(FlaskForm):
    input_id = StringField('Input ID', widget=widgets.HiddenInput())
    name = StringField(
        lazy_gettext('Name'),
        validators=[DataRequired()]
    )
    period = DecimalField(
        TOOLTIPS_INPUT['period']['title'],
        validators=[DataRequired(),
                    validators.NumberRange(
                        min=5.0,
                        max=86400.0
                    )]
    )
    location = StringField(lazy_gettext('Location'))  # Access input (GPIO, I2C address, etc.)
    device_loc = StringField(lazy_gettext('Device Location'))  # Second device location type
    i2c_bus = IntegerField(lazy_gettext('I<sup>2</sup>C Bus'))
    baud_rate = IntegerField(lazy_gettext('Baud Rate'))
    power_output_id = StringField(lazy_gettext('Power Output'))  # For powering input
    calibrate_sensor_measure = StringField(lazy_gettext('Calibration Measurement'))
    resolution = IntegerField(lazy_gettext('Resolution'))
    resolution_2 = IntegerField(lazy_gettext('Resolution'))
    sensitivity = IntegerField(lazy_gettext('Sensitivity'))
    convert_to_unit = StringField(lazy_gettext('Unit'))
    selected_measurement_unit = StringField(lazy_gettext('Unit Measurement'))

    # Server options
    host = StringField(lazy_gettext('Host'))
    port = IntegerField(lazy_gettext('Port'))
    times_check = IntegerField(lazy_gettext('Times to Check'))
    deadline = IntegerField(lazy_gettext('Deadline (seconds)'))

    # Linux Command
    cmd_command = StringField(lazy_gettext('Command'))

    # MAX chip options
    thermocouple_type = StringField(lazy_gettext('RTD Probe Type'))
    ref_ohm = IntegerField(lazy_gettext('Reference Resistance'))

    # SPI Communication
    pin_clock = IntegerField(lazy_gettext('Clock Pin'))
    pin_cs = IntegerField(lazy_gettext('CS Pin'))
    pin_mosi = IntegerField(lazy_gettext('MOSI Pin'))
    pin_miso = IntegerField(lazy_gettext('MISO Pin'))

    # Bluetooth Communication
    bt_adapter = StringField(lazy_gettext('BT Adapter'))

    # ADC
    adc_channel = IntegerField(lazy_gettext('Channel'))
    adc_gain = IntegerField(lazy_gettext('Gain'))
    adc_resolution = IntegerField(lazy_gettext('Resolution'))
    adc_measurement = StringField(lazy_gettext('Measurement'))
    adc_measurement_units = StringField(lazy_gettext('Measurement Units'))
    adc_volts_min = DecimalField(lazy_gettext('Volts Min'))
    adc_volts_max = DecimalField(lazy_gettext('Volts Max'))
    adc_units_min = DecimalField(lazy_gettext('Units Min'))
    adc_units_max = DecimalField(lazy_gettext('Units Max'))
    adc_inverse_unit_scale = BooleanField(lazy_gettext('Inverse Unit Scale'))

    switch_edge = StringField(lazy_gettext('Edge'))
    switch_bounce_time = IntegerField(lazy_gettext('Bounce Time (ms)'))
    switch_reset_period = IntegerField(lazy_gettext('Reset Period'))

    # Pre-Output
    pre_output_id = StringField(TOOLTIPS_INPUT['pre_output_id']['title'])
    pre_output_duration = DecimalField(
        TOOLTIPS_INPUT['pre_output_duration']['title'],
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )]
    )
    pre_output_during_measure = BooleanField(TOOLTIPS_INPUT['pre_output_during_measure']['title'])

    # RPM/Signal
    weighting = DecimalField(lazy_gettext('Weighting'))
    rpm_pulses_per_rev = DecimalField(lazy_gettext('Pulses Per Rev'))
    sample_time = DecimalField(lazy_gettext('Sample Time'))

    # SHT options
    sht_voltage = StringField(lazy_gettext('Voltage'))

    input_mod = SubmitField(lazy_gettext('Save'))
    input_delete = SubmitField(lazy_gettext('Delete'))
    input_activate = SubmitField(lazy_gettext('Activate'))
    input_deactivate = SubmitField(lazy_gettext('Deactivate'))
    input_order_up = SubmitField(lazy_gettext('Up'))
    input_order_down = SubmitField(lazy_gettext('Down'))
