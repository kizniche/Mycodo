# -*- coding: utf-8 -*-
#
# forms_input.py - Input Flask Forms
#

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

from mycodo.config import DEVICES


class InputAdd(FlaskForm):
    input_type = SelectField(
        choices=DEVICES,
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
        lazy_gettext('Period (seconds)'),
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

    # Server options
    host = StringField(lazy_gettext('Host'))
    port = IntegerField(lazy_gettext('Port'))
    times_check = IntegerField(lazy_gettext('Times to Check'))
    deadline = IntegerField(lazy_gettext('Deadline (seconds)'))

    # Linux Command
    cmd_command = StringField(lazy_gettext('Command'))
    cmd_measurement = StringField(lazy_gettext('Measurement'))
    cmd_measurement_units = StringField(lazy_gettext('Unit'))

    # MAX chip options
    thermocouple_type = StringField(lazy_gettext('RTD Probe Type'))
    ref_ohm = IntegerField(lazy_gettext('Reference Resistance (Ohm)'))

    # SPI Communication
    pin_clock = IntegerField(lazy_gettext('Clock Pin'))
    pin_cs = IntegerField(lazy_gettext('CS Pin'))
    pin_mosi = IntegerField(lazy_gettext('MOSI Pin'))
    pin_miso = IntegerField(lazy_gettext('MISO Pin'))

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
    pre_output_id = StringField(lazy_gettext('Pre Output'))
    pre_output_duration = DecimalField(
        lazy_gettext('Pre Out Duration'),
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )]
    )
    pre_output_during_measure = BooleanField(lazy_gettext('Pre During Measure'))

    # RPM/Signal
    weighting = DecimalField(lazy_gettext('Weighting'))
    rpm_pulses_per_rev = DecimalField(lazy_gettext('Pulses Per Rev'))
    sample_time = DecimalField(lazy_gettext('Sample Time (seconds)'))

    # SHT options
    sht_voltage = StringField(lazy_gettext('Voltage'))

    input_mod = SubmitField(lazy_gettext('Save'))
    input_delete = SubmitField(lazy_gettext('Delete'))
    input_activate = SubmitField(lazy_gettext('Activate'))
    input_deactivate = SubmitField(lazy_gettext('Deactivate'))
    input_order_up = SubmitField(lazy_gettext('Up'))
    input_order_down = SubmitField(lazy_gettext('Down'))
