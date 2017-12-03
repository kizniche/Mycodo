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
from wtforms import SubmitField
from wtforms import StringField
from wtforms import validators
from wtforms import widgets

from wtforms.validators import DataRequired

from mycodo.config import INPUTS


class InputAdd(FlaskForm):
    numberSensors = IntegerField(
        lazy_gettext(u'Quantity'),
        render_kw={"placeholder": lazy_gettext(u"Quantity")},
        validators=[validators.NumberRange(
            min=1,
            max=20
        )]
    )
    sensor = SelectField(
        choices=INPUTS,
        validators=[DataRequired()]
    )
    sensorAddSubmit = SubmitField(lazy_gettext(u'Add Device'))


class InputMod(FlaskForm):
    modSensor_id = IntegerField('Input ID', widget=widgets.HiddenInput())
    name = StringField(
        lazy_gettext(u'Name'),
        validators=[DataRequired()]
    )
    i2c_bus = IntegerField(lazy_gettext(u'I<sup>2</sup>C Bus'))
    location = StringField(lazy_gettext(u'Location'))
    baud_rate = IntegerField(lazy_gettext(u'Baud Rate'))
    device_loc = StringField(lazy_gettext(u'Device Location'))
    calibrate_sensor_measure = StringField(lazy_gettext(u'Calibration Measurement'))
    resolution = IntegerField(lazy_gettext(u'Resolution'))
    sensitivity = IntegerField(lazy_gettext(u'Sensitivity'))
    power_relay_id = IntegerField(lazy_gettext(u'Power Output'))
    multiplexer_address = StringField(lazy_gettext(u'Multiplexer (MX)'))
    multiplexer_bus = StringField(lazy_gettext(u'Mx I<sup>2</sup>C Bus'))
    multiplexer_channel = IntegerField(lazy_gettext(u'Mx Channel'))
    cmd_command = StringField(lazy_gettext(u'Command'))
    cmd_measurement = StringField(lazy_gettext(u'Measurement'))
    cmd_measurement_units = StringField(lazy_gettext(u'Unit'))
    adc_channel = IntegerField(lazy_gettext(u'Channel'))
    adc_gain = IntegerField(lazy_gettext(u'Gain'))
    adc_resolution = IntegerField(lazy_gettext(u'Resolution'))
    adc_measurement = StringField(lazy_gettext(u'Measurement'))
    adc_measurement_units = StringField(lazy_gettext(u'Measurement Units'))
    adc_volts_min = DecimalField(lazy_gettext(u'Volts Min'))
    adc_volts_max = DecimalField(lazy_gettext(u'Volts Max'))
    adc_units_min = DecimalField(lazy_gettext(u'Units Min'))
    adc_units_max = DecimalField(lazy_gettext(u'Units Max'))
    adc_inverse_unit_scale = BooleanField(lazy_gettext(u'Inverse Unit Scale'))
    switch_edge = StringField(lazy_gettext(u'Edge'))
    switch_bounce_time = IntegerField(lazy_gettext(u'Bounce Time (ms)'))
    switch_reset_period = IntegerField(lazy_gettext(u'Reset Period'))
    pre_relay_id = StringField(lazy_gettext(u'Pre Output'))
    pre_relay_duration = DecimalField(
        lazy_gettext(u'Pre Output Duration'),
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )]
    )
    period = DecimalField(
        lazy_gettext(u'Period (seconds)'),
        validators=[DataRequired(),
                    validators.NumberRange(
            min=5.0,
            max=86400.0
        )]
    )
    weighting = DecimalField(lazy_gettext(u'Weighting'))
    rpm_pulses_per_rev = DecimalField(lazy_gettext(u'Pulses Per Rev'))
    sample_time = DecimalField(lazy_gettext(u'Sample Time (seconds)'))
    sht_clock_pin = IntegerField(
        lazy_gettext(u'Clock Pin'),
        validators=[validators.NumberRange(
            min=0,
            max=100,
            message=lazy_gettext(u"If using a SHT sensor, enter the GPIO "
                                 u"connected to the clock pin (using BCM "
                                 u"numbering)")
        )]
    )
    sht_voltage = StringField(lazy_gettext(u'Voltage'))
    modSensorSubmit = SubmitField(lazy_gettext(u'Save'))
    delSensorSubmit = SubmitField(lazy_gettext(u'Delete'))
    activateSensorSubmit = SubmitField(lazy_gettext(u'Activate'))
    deactivateSensorSubmit = SubmitField(lazy_gettext(u'Deactivate'))
    orderSensorUp = SubmitField(lazy_gettext(u'Up'))
    orderSensorDown = SubmitField(lazy_gettext(u'Down'))

    conditional_type = StringField('Conditional Type', widget=widgets.HiddenInput())
    sensorCondAddSubmit = SubmitField(lazy_gettext(u'Add Conditional'))
