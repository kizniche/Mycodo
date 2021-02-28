# coding=utf-8
#
#  bang_bang.py - A hysteretic control
#
#  Copyright (C) 2015-2020 Rob Bultman <rob@firstbuild.com>
#
import threading
import time
import timeit

from flask_babel import lazy_gettext

from mycodo.config import SQL_DATABASE_MYCODO
from mycodo.controllers.base_controller import AbstractController
from mycodo.databases.models import CustomController
from mycodo.databases.utils import session_scope
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.database import db_retrieve_table_daemon

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO

def constraints_pass_positive_value(mod_controller, value):
    """
    Check if the user controller is acceptable
    :param mod_controller: SQL object with user-saved Input options
    :param value: float or int
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure value is positive
    if value <= 0:
        all_passed = False
        errors.append("Must be a positive value")
    return all_passed, errors, mod_controller


FUNCTION_INFORMATION = {
    'function_name_unique': 'bang_bang',
    'function_name': 'Bang-Bang Hysteretic',

    'message': 'A simple bang-bang control for controlling one output from one input.'
        ' Select an input, an output, enter a setpoint and a hysteresis, and select a direction.'
        ' The output will turn on when the input is below setpoint-hysteresis and turn off when'
        ' the input is above setpoint+hysteresis. This is the behavior when Raise is selected, such'
        ' as when heating. Lower direction has the opposite behavior - it will try to'
        ' turn the output on in order to drive the input lower.',

    'options_enabled': [],
    'dependencies_module': [],

    'custom_options': [
        {
            'id': 'measurement',
            'type': 'select_measurement',
            'default_value': '',
            'required': True,
            'options_select': [
                'Input',
                'Math',
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


class CustomModule(AbstractController, threading.Thread):
    """
    Class to operate custom controller
    """
    def __init__(self, ready, unique_id, testing=False):
        threading.Thread.__init__(self)
        super(CustomModule, self).__init__(ready, unique_id=unique_id, name=__name__)

        self.unique_id = unique_id
        self.log_level_debug = None
        self.control_variable = None
        self.timestamp = None
        self.timer = None
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
            CustomController, unique_id=unique_id)
        self.setup_custom_options(
            FUNCTION_INFORMATION['custom_options'], custom_function)

        self.output_channel = self.get_output_channel_from_channel_id(
            self.output_channel_id)

        self.initialize_variables()

    def initialize_variables(self):
        controller = db_retrieve_table_daemon(
            CustomController, unique_id=self.unique_id)
        self.log_level_debug = controller.log_level_debug
        self.set_log_level_debug(self.log_level_debug)

        self.timestamp = time.time()

    def run(self):
        try:
            if self.output_channel is None:
                self.logger.error("Cannot start bang-bang controller: Could not find output channel.")
                self.deactivate_self()
                return

            self.logger.info("Activated in {:.1f} ms".format(
                (timeit.default_timer() - self.thread_startup_timer) * 1000))

            self.ready.set()
            self.running = True
            self.timer = time.time()

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

            # Start a loop
            while self.running:
                if self.timer_loop < time.time():
                    while self.timer_loop < time.time():
                        self.timer_loop += self.update_period
                    self.loop()
                time.sleep(0.1)
        except:
            self.logger.exception("Run Error")
        finally:
            self.run_finally()
            self.running = False
            if self.thread_shutdown_timer:
                self.logger.info("Deactivated in {:.1f} ms".format(
                    (timeit.default_timer() - self.thread_shutdown_timer) * 1000))
            else:
                self.logger.error("Deactivated unexpectedly")

    def loop(self):
        last_measurement = self.get_last_measurement(
            self.measurement_device_id,
            self.measurement_measurement_id)[1]
        outputState = self.control.output_state(self.output_device_id, self.output_channel)

        self.logger.info("Input: {}, output: {}, target: {}, hyst: {}".format(
            last_measurement, outputState, self.setpoint, self.hysteresis))

        if self.direction == 'raise':
            if outputState == 'on':
                # looking to turn output off
                if last_measurement > (self.setpoint + self.hysteresis):
                    self.control.output_off(
                        self.output_device_id,
                        output_channel=self.output_channel)
            else:
                # looking to turn output on
                if last_measurement < (self.setpoint - self.hysteresis):
                    self.control.output_on(
                        self.output_device_id,
                        output_channel=self.output_channel)
        elif self.direction == 'lower':
            if outputState == 'on':
                # looking to turn output off
                if last_measurement < (self.setpoint - self.hysteresis):
                    self.control.output_off(
                        self.output_device_id,
                        output_channel=self.output_channel)
            else:
                # looking to turn output on
                if last_measurement > (self.setpoint + self.hysteresis):
                    self.control.output_on(
                        self.output_device_id,
                        output_channel=self.output_channel)
        else:
            self.logger.info("Unknown controller direction: {}".format(self.direction))

    def deactivate_self(self):
        self.logger.info("Deactivating bang-bang controller")

        with session_scope(MYCODO_DB_PATH) as new_session:
            mod_cont = new_session.query(CustomController).filter(
                CustomController.unique_id == self.unique_id).first()
            mod_cont.is_activated = False
            new_session.commit()

        deactivate_controller = threading.Thread(
            target=self.control.controller_deactivate,
            args=(self.unique_id,))
        deactivate_controller.start()

    def pre_stop(self):
        self.control.output_off(self.output_device_id, self.output_channel)
