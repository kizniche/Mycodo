# coding=utf-8
#
#  bang_bang_pwm.py - A hysteretic control for PWM Outputs
import time

from flask_babel import lazy_gettext

from mycodo.databases.models import CustomController
from mycodo.functions.base_function import AbstractFunction
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.constraints_pass import constraints_pass_positive_value
from mycodo.utils.database import db_retrieve_table_daemon

FUNCTION_INFORMATION = {
    'function_name_unique': 'bang_bang_pwm',
    'function_name': 'Bang-Bang Hysteretic (PWM) (Raise/Lower/Both)',

    'message': 'A simple bang-bang control for controlling one PWM output from one input.'
        ' Select an input, a PWM output, enter a setpoint and a hysteresis, and select a direction.'
        ' The output will turn on when the input is below below (lower = setpoint - hysteresis) and turn off when'
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
            'phrase': 'Select a measurement the selected output will affect'
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
            'phrase': 'Select an output to control that will affect the measurement'
        },
        {
            'id': 'setpoint',
            'type': 'float',
            'default_value': 50,
            'required': True,
            'name': lazy_gettext('Setpoint'),
            'phrase': 'The desired setpoint'
        },
        {
            'id': 'hysteresis',
            'type': 'float',
            'default_value': 1,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': lazy_gettext('Hysteresis'),
            'phrase': 'The amount above and below the setpoint that defines the control band'
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
        },
        {
            'id': 'duty_cycle_increase',
            'type': 'float',
            'default_value': 90,
            'required': True,
            'name': 'Duty Cycle (increase)',
            'phrase': 'The duty cycle to increase the measurement'
        },
        {
            'id': 'duty_cycle_maintain',
            'type': 'float',
            'default_value': 55,
            'required': True,
            'name': 'Duty Cycle (maintain)',
            'phrase': 'The duty cycle to maintain the measurement'
        },
        {
            'id': 'duty_cycle_decrease',
            'type': 'float',
            'default_value': 20,
            'required': True,
            'name': 'Duty Cycle (decrease)',
            'phrase': 'The duty cycle to decrease the measurement'
        },
        {
            'id': 'duty_cycle_shutdown',
            'type': 'float',
            'default_value': 0,
            'required': True,
            'name': 'Duty Cycle (shutdown)',
            'phrase': 'The duty cycle to set when the function shuts down'
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
        self.duty_cycle_increase = None
        self.duty_cycle_maintain = None
        self.duty_cycle_decrease = None
        self.duty_cycle_shutdown = None

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
            "Direction: {}, Increase: {}%, Maintain: {}%, Decrease: {}%, "
            "Shutdown: {}%, Period: {}".format(
                self.measurement_device_id,
                self.measurement_measurement_id,
                self.output_device_id,
                self.output_channel,
                self.setpoint,
                self.hysteresis,
                self.direction,
                self.duty_cycle_increase,
                self.duty_cycle_maintain,
                self.duty_cycle_decrease,
                self.duty_cycle_shutdown,
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
            if last_measurement < (self.setpoint - self.hysteresis):
                self.control.output_on(
                    self.output_device_id,
                    output_type='pwm',
                    amount=self.duty_cycle_increase,
                    output_channel=self.output_channel)
            else:
                self.control.output_on(
                    self.output_device_id,
                    output_type='pwm',
                    amount=self.duty_cycle_maintain,
                    output_channel=self.output_channel)
        elif self.direction == 'lower':
            if last_measurement > (self.setpoint + self.hysteresis):
                self.control.output_on(
                    self.output_device_id,
                    output_type='pwm',
                    amount=self.duty_cycle_decrease,
                    output_channel=self.output_channel)
            else:
                self.control.output_on(
                    self.output_device_id,
                    output_type='pwm',
                    amount=self.duty_cycle_maintain,
                    output_channel=self.output_channel)
        elif self.direction == 'both':
            if last_measurement < (self.setpoint - self.hysteresis):
                self.control.output_on(
                    self.output_device_id,
                    output_type='pwm',
                    amount=self.duty_cycle_increase,
                    output_channel=self.output_channel)
            elif last_measurement > (self.setpoint + self.hysteresis):
                self.control.output_on(
                    self.output_device_id,
                    output_type='pwm',
                    amount=self.duty_cycle_decrease,
                    output_channel=self.output_channel)
            else:
                self.control.output_on(
                    self.output_device_id,
                    output_type='pwm',
                    amount=self.duty_cycle_maintain,
                    output_channel=self.output_channel)
        else:
            self.logger.info("Unknown controller direction: '{}'".format(self.direction))

    def stop_function(self):
        self.control.output_on(
            self.output_device_id,
            output_type='pwm',
            amount=self.duty_cycle_shutdown,
            output_channel=self.output_channel)
