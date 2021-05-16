# coding=utf-8
#
#  bang_bang.py - A hysteretic control for On/Off Outputs
#
#  Copyright (C) 2015-2020 Rob Bultman <rob@firstbuild.com>
#
import time

from flask_babel import lazy_gettext

from mycodo.config import SQL_DATABASE_MYCODO
from mycodo.databases.models import CustomController
from mycodo.functions.base_function import AbstractFunction
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.constraints_pass import constraints_pass_positive_value
from mycodo.utils.database import db_retrieve_table_daemon

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO


# TODO: Remove this at next major version (obsolete because a On/Off Raise/Lower/Both Bang-Bang exists
FUNCTION_INFORMATION = {
    'function_name_unique': 'bang_bang',
    'function_name': 'Bang-Bang Hysteretic (On/Off) (Raise/Lower)',

    'message': 'A simple bang-bang control for controlling one output from one input.'
        ' Select an input, an output, enter a setpoint and a hysteresis, and select a direction.'
        ' The output will turn on when the input is below (lower = setpoint - hysteresis) and turn off when'
        ' the input is above (higher = setpoint + hysteresis). This is the behavior when Raise is selected, such'
        ' as when heating. Lower direction has the opposite behavior - it will try to'
        ' turn the output on in order to drive the input lower.',

    'options_disabled': [
        'measurements_select',
        'measurements_configure'
    ],

    'custom_options': [
        {
            'id': 'measurement',
            'type': 'select_measurement',
            'default_value': '',
            'required': True,
            'options_select': [
                'Input',
                'Math',
                'Function'
            ],
            'name': lazy_gettext('Measurement'),
            'phrase': lazy_gettext('Select a measurement the selected output will affect')
        },
        {
            'id': 'output',
            'type': 'select_measurement_channel',
            'default_value': '',
            'required': True,
            'options_select': [
                'Output_Channels_Measurements',
            ],
            'name': lazy_gettext('Output'),
            'phrase': lazy_gettext('Select an output to control that will affect the measurement')
        },
        {
            'id': 'setpoint',
            'type': 'float',
            'default_value': 50,
            'required': True,
            'name': lazy_gettext('Setpoint'),
            'phrase': lazy_gettext('The desired setpoint')
        },
        {
            'id': 'hysteresis',
            'type': 'float',
            'default_value': 1,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': lazy_gettext('Hysteresis'),
            'phrase': lazy_gettext('The amount above and below the setpoint that defines the control band')
        },
        {
            'id': 'direction',
            'type': 'select',
            'default_value': 'raise',
            'required': True,
            'options_select': [
                ('raise', 'Raise'),
                ('lower', 'Lower')
            ],
            'name': lazy_gettext('Direction'),
            'phrase': 'Raise means the measurement will increase when the control is on (heating). Lower means the measurement will decrease when the output is on (cooling)'
        },
        {
            'id': 'update_period',
            'type': 'float',
            'default_value': 5,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': lazy_gettext('Period (seconds)'),
            'phrase': lazy_gettext('The duration (seconds) between measurements or actions')
        }
    ]
}


class CustomModule(AbstractFunction):
    """
    Class to operate custom controller
    """
    def __init__(self, function, testing=False):
        super(CustomModule, self).__init__(function, testing=testing, name=__name__)

        self.control_variable = None
        self.timestamp = None
        self.control = DaemonControl()
        self.outputIsOn = False
        self.timer_loop = time.time()

        # Initialize custom options
        self.measurement_device_id = None
        self.measurement_measurement_id = None
        self.output_device_id = None
        self.output_measurement_id = None
        self.output_channel_id = None
        self.setpoint = None
        self.hysteresis = None
        self.direction = None
        self.output_channel = None
        self.update_period = None

        # Set custom options
        custom_function = db_retrieve_table_daemon(
            CustomController, unique_id=self.unique_id)
        self.setup_custom_options(
            FUNCTION_INFORMATION['custom_options'], custom_function)

        if not testing:
            self.initialize_variables()

    def initialize_variables(self):
        self.timestamp = time.time()

        self.output_channel = self.get_output_channel_from_channel_id(
            self.output_channel_id)

        self.logger.info(
            "Bang-Bang controller started with options: "
            "Measurement Device: {}, Measurement: {}, Output: {}, "
            "Output_Channel: {}, Setpoint: {}, Hysteresis: {}, "
            "Direction: {}, Period: {}".format(
                self.measurement_device_id,
                self.measurement_measurement_id,
                self.output_device_id,
                self.output_channel,
                self.setpoint,
                self.hysteresis,
                self.direction,
                self.update_period))

    def loop(self):
        if self.timer_loop > time.time():
            return

        while self.timer_loop < time.time():
            self.timer_loop += self.update_period

        if self.output_channel is None:
            self.logger.error("Cannot run bang-bang controller: Check output channel.")
            return

        last_measurement = self.get_last_measurement(
            self.measurement_device_id,
            self.measurement_measurement_id)[1]
        outputState = self.control.output_state(self.output_device_id, self.output_channel)

        self.logger.info("Input: {}, output: {}, target: {}, hyst: {}".format(
            last_measurement, outputState, self.setpoint, self.hysteresis))

        if self.direction == 'raise':
            if last_measurement > (self.setpoint + self.hysteresis):
                if outputState == 'on':
                    self.control.output_off(
                        self.output_device_id,
                        output_channel=self.output_channel)
            else:
                if last_measurement < (self.setpoint - self.hysteresis):
                    self.control.output_on(
                        self.output_device_id,
                        output_channel=self.output_channel)
        elif self.direction == 'lower':
            if last_measurement < (self.setpoint - self.hysteresis):
                if outputState == 'on':
                    self.control.output_off(
                        self.output_device_id,
                        output_channel=self.output_channel)
            else:
                if last_measurement > (self.setpoint + self.hysteresis):
                    self.control.output_on(
                        self.output_device_id,
                        output_channel=self.output_channel)
        else:
            self.logger.info("Unknown controller direction: '{}'".format(self.direction))

    def stop_function(self):
        self.control.output_off(self.output_device_id, self.output_channel)
