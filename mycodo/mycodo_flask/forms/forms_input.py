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

from mycodo.config import INPUTS


class InputAdd(FlaskForm):
    numberSensors = IntegerField(
        lazy_gettext('Quantity'),
        render_kw={"placeholder": lazy_gettext("Quantity")},
        validators=[validators.NumberRange(
            min=1,
            max=20
        )]
    )
    sensor = SelectField(
        choices=INPUTS,
        validators=[DataRequired()]
    )
    sensorAddSubmit = SubmitField(lazy_gettext('Add Input'))


class InputMod(FlaskForm):
    modSensor_id = IntegerField('Input ID', widget=widgets.HiddenInput())
    name = StringField(
        lazy_gettext('Name'),
        validators=[DataRequired()]
    )
    i2c_bus = IntegerField(lazy_gettext('I<sup>2</sup>C Bus'))
    location = StringField(lazy_gettext('Location'))
    baud_rate = IntegerField(lazy_gettext('Baud Rate'))
    device_loc = StringField(lazy_gettext('Device Location'))
    calibrate_sensor_measure = StringField(lazy_gettext('Calibration Measurement'))
    resolution = IntegerField(lazy_gettext('Resolution'))
    sensitivity = IntegerField(lazy_gettext('Sensitivity'))
    power_relay_id = IntegerField(lazy_gettext('Power Output'))
    multiplexer_address = StringField(lazy_gettext('Multiplexer (MX)'))
    multiplexer_bus = StringField(lazy_gettext('Mx I<sup>2</sup>C Bus'))
    multiplexer_channel = IntegerField(lazy_gettext('Mx Channel'))
    cmd_command = StringField(lazy_gettext('Command'))
    cmd_measurement = StringField(lazy_gettext('Measurement'))
    cmd_measurement_units = StringField(lazy_gettext('Unit'))
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
    pre_relay_id = StringField(lazy_gettext('Pre Output'))
    pre_relay_duration = DecimalField(
        lazy_gettext('Pre Output Duration'),
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )]
    )
    period = DecimalField(
        lazy_gettext('Period (seconds)'),
        validators=[DataRequired(),
                    validators.NumberRange(
            min=5.0,
            max=86400.0
        )]
    )
    weighting = DecimalField(lazy_gettext('Weighting'))
    rpm_pulses_per_rev = DecimalField(lazy_gettext('Pulses Per Rev'))
    sample_time = DecimalField(lazy_gettext('Sample Time (seconds)'))
    sht_clock_pin = IntegerField(
        lazy_gettext('Clock Pin'),
        validators=[validators.NumberRange(
            min=0,
            max=100,
            message=lazy_gettext("If using a SHT sensor, enter the GPIO "
                                 "connected to the clock pin (using BCM "
                                 "numbering)")
        )]
    )
    sht_voltage = StringField(lazy_gettext('Voltage'))
    modSensorSubmit = SubmitField(lazy_gettext('Save'))
    delSensorSubmit = SubmitField(lazy_gettext('Delete'))
    activateSensorSubmit = SubmitField(lazy_gettext('Activate'))
    deactivateSensorSubmit = SubmitField(lazy_gettext('Deactivate'))
    orderSensorUp = SubmitField(lazy_gettext('Up'))
    orderSensorDown = SubmitField(lazy_gettext('Down'))
    sensorCondAddSubmit = SubmitField(lazy_gettext('Add Conditional'))
