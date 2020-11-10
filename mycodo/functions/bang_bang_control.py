# coding=utf-8
#
#  bang_bang_control.py - A hysteretic control
#
#  Copyright (C) 2015-2020 Rob Bultman <rob@firstbuild.com>
#
import threading
import time
import timeit

from flask_babel import lazy_gettext

from mycodo.controllers.base_controller import AbstractController
from mycodo.databases.models import CustomController
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.database import db_retrieve_table_daemon


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
    'function_name': 'Bang-Bang (Hysteretic) Control',

    'message': 'A simple bang-bang control for controlling one output from one input.',

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
            'type': 'select_device',
            'default_value': '',
            'required': True,
            'options_select': [
                'Output',
            ],
            'name': lazy_gettext('Output'),
            'phrase': lazy_gettext('Select an output to control that will affect the measurement')
        },
        {
            'id': 'setpoint',
            'type': 'float',
            'default_value': 50,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': lazy_gettext('Setpoint'),
            'phrase': lazy_gettext('The desired setpoint in degrees F')
        },
        {
            'id': 'hysteresis',
            'type': 'float',
            'default_value': 0.5,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': lazy_gettext('Hysteresis'),
            'phrase': lazy_gettext('The amount above and below the setpoint that defines the control band')
        },
        {
            'id': 'direction',
            'type': 'select',
            'default_value': 'direct',
            'options_select': [
                ('direct', 'inverse')
            ],
            'name': lazy_gettext('Direction'),
            'phrase': lazy_gettext('Direct means the measurement will increase when the control is on (heating), inverse means the measurement will decrease when the output is on (cooling)')
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

        # Initialize custom options
        self.measurement_device_id = None
        self.measurement_measurement_id = None
        self.output_id = None
        self.setpoint = None
        self.hysteresis = None
        self.direction = None

        # Set custom options
        custom_function = db_retrieve_table_daemon(
            CustomController, unique_id=unique_id)
        self.setup_custom_options(
            FUNCTION_INFORMATION['custom_options'], custom_function)

        self.initialize_variables()

    def initialize_variables(self):
        controller = db_retrieve_table_daemon(
            CustomController, unique_id=self.unique_id)
        self.log_level_debug = controller.log_level_debug
        self.set_log_level_debug(self.log_level_debug)

        self.timestamp = time.time()

    def run(self):
        try:
            self.logger.info("Activated in {:.1f} ms".format(
                (timeit.default_timer() - self.thread_startup_timer) * 1000))

            self.ready.set()
            self.running = True
            self.timer = time.time()

            self.logger.info(
                "Band-Bang controller started with options: "
                "Measurement Device: {}, Measurement: {}, Output: {}, Setpoint: {}, "
                "Hysteresis: {}, Direction: {}".format(
                    self.measurement_device_id,
                    self.measurement_measurement_id,
                    self.output_id,
                    self.setpoint,
                    self.hysteresis,
                    self.direction))

            # Start a loop
            while self.running:
                self.loop()
                time.sleep(5)
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
        self.logger.info("Bang bang controller loop running")

    def deactivate_self(self):
        self.logger.info("Deactivating bang-bang controller")

        from mycodo.databases.utils import session_scope
        from mycodo.config import SQL_DATABASE_MYCODO
        MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO
        with session_scope(MYCODO_DB_PATH) as new_session:
            mod_cont = new_session.query(CustomController).filter(
                CustomController.unique_id == self.unique_id).first()
            mod_cont.is_activated = False
            new_session.commit()

        deactivate_controller = threading.Thread(
            target=self.control.controller_deactivate,
            args=(self.unique_id,))
        deactivate_controller.start()