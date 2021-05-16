# coding=utf-8
#
#  bang_bang_on_off.py - A hysteretic control for On/Off Outputs
import time

from flask_babel import lazy_gettext

from mycodo.config import SQL_DATABASE_MYCODO
from mycodo.databases.models import CustomController
from mycodo.functions.base_function import AbstractFunction
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.constraints_pass import constraints_pass_positive_value
from mycodo.utils.database import db_retrieve_table_daemon

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO


FUNCTION_INFORMATION = {
    'function_name_unique': 'bang_bang_on_off',
    'function_name': 'Bang-Bang Hysteretic (On/Off) (Raise/Lower/Both)',

    'message': 'A simple bang-bang control for controlling one output from one input.'
        ' Select an input, an output, enter a setpoint and a hysteresis, and select a direction.'
        ' The output will turn on when the input is below (lower = setpoint - hysteresis) and turn off when'
        ' the input is above (higher = setpoint + hysteresis). This is the behavior when Raise is selected, such'
        ' as when heating. Lower direction has the opposite behavior - it will try to'
        ' turn the output on in order to drive the input lower. The Both option will raise and lower.',

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
            'id': 'output_raise',
            'type': 'select_measurement_channel',
            'default_value': '',
            'required': True,
            'options_select': [
                'Output_Channels_Measurements',
            ],
            'name': 'Output (Raise)',
            'phrase': 'Select an output to control that will raise the measurement'
        },
        {
            'id': 'output_lower',
            'type': 'select_measurement_channel',
            'default_value': '',
            'required': True,
            'options_select': [
                'Output_Channels_Measurements',
            ],
            'name': 'Output (Lower)',
            'phrase': 'Select an output to control that will lower the measurement'
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
            'default_value': 'both',
            'required': True,
            'options_select': [
                ('raise', 'Raise'),
                ('lower', 'Lower'),
                ('both', 'Both')
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
        self.timer_loop = time.time()

        # Initialize custom options
        self.measurement_device_id = None
        self.measurement_measurement_id = None
        self.output_raise_device_id = None
        self.output_raise_measurement_id = None
        self.output_raise_channel_id = None
        self.output_lower_device_id = None
        self.output_lower_measurement_id = None
        self.output_lower_channel_id = None
        self.setpoint = None
        self.hysteresis = None
        self.direction = None
        self.output_raise_channel = None
        self.output_lower_channel = None
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

        self.output_raise_channel = self.get_output_channel_from_channel_id(
            self.output_raise_channel_id)
        self.output_lower_channel = self.get_output_channel_from_channel_id(
            self.output_lower_channel_id)

        self.logger.info(
            "Bang-Bang controller started with options: "
            "Measurement Device: {}, Measurement: {},"
            "Output Raise: {}, Output_Raise_Channel: {},"
            "Output Lower: {}, Output_Lower_Channel: {},"
            "Setpoint: {}, Hysteresis: {}, "
            "Direction: {}, Period: {}".format(
                self.measurement_device_id,
                self.measurement_measurement_id,
                self.output_raise_device_id,
                self.output_raise_channel,
                self.output_lower_device_id,
                self.output_lower_channel,
                self.setpoint,
                self.hysteresis,
                self.direction,
                self.update_period))

    def loop(self):
        if self.timer_loop > time.time():
            return

        while self.timer_loop < time.time():
            self.timer_loop += self.update_period

        if ((self.direction == 'raise' and self.output_raise_channel is None) or
                (self.direction == 'lower' and self.output_lower_channel is None) or
                self.direction == 'both' and None in [self.output_raise_channel, self.output_lower_channel]):
            self.logger.error("Cannot start bang-bang controller: Check output channel(s).")
            return

        last_measurement = self.get_last_measurement(
            self.measurement_device_id,
            self.measurement_measurement_id)[1]

        output_raise_state = self.control.output_state(
            self.output_raise_device_id, self.output_raise_channel)
        output_lower_state = self.control.output_state(
            self.output_lower_device_id, self.output_raise_channel)

        self.logger.info(
            "Input: {}, output_raise: {}, output_lower: {}, target: {}, hyst: {}".format(
                last_measurement,
                output_raise_state,
                output_lower_state,
                self.setpoint,
                self.hysteresis))

        if self.direction == 'raise':
            if last_measurement > (self.setpoint + self.hysteresis):
                if output_raise_state == 'on':
                    self.control.output_off(
                        self.output_raise_device_id,
                        output_channel=self.output_raise_channel)
            elif last_measurement < (self.setpoint - self.hysteresis):
                self.control.output_on(
                    self.output_raise_device_id,
                    output_channel=self.output_raise_channel)
        elif self.direction == 'lower':
            if last_measurement < (self.setpoint - self.hysteresis):
                if output_lower_state == 'on':
                    self.control.output_off(
                        self.output_lower_device_id,
                        output_channel=self.output_lower_channel)
            elif last_measurement > (self.setpoint + self.hysteresis):
                self.control.output_on(
                    self.output_lower_device_id,
                    output_channel=self.output_lower_channel)
        elif self.direction == 'both':
            if (last_measurement > (self.setpoint - self.hysteresis) or
                    last_measurement < (self.setpoint + self.hysteresis)):
                if output_raise_state == 'on':
                    self.control.output_off(
                        self.output_raise_device_id,
                        output_channel=self.output_raise_channel)
                if output_lower_state == 'on':
                    self.control.output_off(
                        self.output_lower_device_id,
                        output_channel=self.output_lower_channel)
            elif last_measurement > (self.setpoint + self.hysteresis):
                self.control.output_on(
                    self.output_lower_device_id,
                    output_channel=self.output_lower_channel)
            elif last_measurement < (self.setpoint - self.hysteresis):
                self.control.output_on(
                    self.output_raise_device_id,
                    output_channel=self.output_raise_channel)
        else:
            self.logger.info(
                "Unknown controller direction: '{}'".format(self.direction))

    def stop_function(self):
        self.control.output_off(
            self.output_raise_device_id, self.output_raise_channel)
        self.control.output_off(
            self.output_lower_device_id, self.output_lower_channel)
