# coding=utf-8
#
#  custom_function_example.py - Custom function example file for importing into Mycodo
#
#  Copyright (C) 2015-2020 Kyle T. Gabriel <mycodo@kylegabriel.com>
#
#  This file is part of Mycodo
#
#  Mycodo is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Mycodo is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Mycodo. If not, see <http://www.gnu.org/licenses/>.
#
#  Contact at kylegabriel.com
#
import threading
import time
import timeit

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
    'function_name_unique': 'example_function_generic',
    'function_name': 'Function: Example: Generic',

    'message': 'This is a custom message that will appear above the Function options. It merely demonstrates how to generate user options and manipulate them. It will retrieve the last selected measurement, turn the selected output on for 15 seconds, then deactivate itself. Study the code to develop your own Custom Function.',

    'options_enabled': [
        'custom_options'
    ],

    'dependencies_module': [
        # Example dependencies that will be installed when the user adds the controller
        # ('apt', 'build-essential', 'build-essential'),
        # ('apt', 'bison', 'bison'),
        # ('apt', 'libasound2-dev', 'libasound2-dev'),
        # ('apt', 'libpulse-dev', 'libpulse-dev'),
        # ('apt', 'swig', 'swig'),
        # ('pip-pypi', 'pocketsphinx', 'pocketsphinx')
    ],

    'custom_options': [
        {
            'id': 'text_1',
            'type': 'text',
            'default_value': 'Text_1',
            'required': True,
            'name': 'Text 1',
            'phrase': 'Text 1 Description'
        },
        {
            'id': 'integer_1',
            'type': 'integer',
            'default_value': 100,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Integer 1',
            'phrase': 'Integer 1 Description'
        },
        {
            'id': 'float_1',
            'type': 'float',
            'default_value': 50.2,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Float 1',
            'phrase': 'Float 1 Description'
        },
        {
            'id': 'bool_1',
            'type': 'bool',
            'default_value': True,
            'name': 'Boolean 1',
            'phrase': 'Boolean 1 Description'
        },
        {
            'id': 'select_1',
            'type': 'select',
            'default_value': 'SECOND',
            'options_select': [
                ('FIRST', 'First Option Selected'),
                ('SECOND', 'Second Option Selected'),
                ('THIRD', 'Third Option Selected'),
            ],
            'name': 'Select 1',
            'phrase': 'Select 1 Description'
        },
        {
            'id': 'select_measurement_1',
            'type': 'select_measurement',
            'default_value': '',
            'options_select': [
                'Input',
                'Math',
                'PID'
            ],
            'name': 'Select Measurement 1',
            'phrase': 'Select Measurement 1 Description'
        },
        {
            'id': 'output_1',
            'type': 'select_measurement_channel',
            'default_value': '',
            'required': True,
            'options_select': [
                'Output_Channels_Measurements',
            ],
            'name': 'Output',
            'phrase': 'Select an output to modulate that will affect the measurement'
        },
        {
            'id': 'select_device_1',
            'type': 'select_device',
            'default_value': '',
            'options_select': [
                'Output',
            ],
            'name': 'Select Device 1',
            'phrase': 'Select Device 1 Description'
        },
        {
            'id': 'select_device_2',
            'type': 'select_device',
            'default_value': '',
            'options_select': [
                'Input',
                'Output',
                'Math',
                'Function',
                'PID',
                'Trigger'
            ],
            'name': 'Select Device 2',
            'phrase': 'Select Device 2 Description'
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

        self.control = DaemonControl()

        # Initialize custom options
        self.text_1 = None
        self.integer_1 = None
        self.float_1 = None
        self.bool_1 = None
        self.select_1 = None
        self.select_measurement_1_device_id = None
        self.select_measurement_1_measurement_id = None
        self.output_1_device_id = None
        self.output_1_measurement_id = None
        self.output_1_channel_id = None
        self.select_device_1_id = None
        self.select_device_2_id = None

        # Set custom options
        custom_function = db_retrieve_table_daemon(
            CustomController, unique_id=unique_id)
        self.setup_custom_options(
            FUNCTION_INFORMATION['custom_options'], custom_function)

        # Get selected output channel number
        self.output_1_channel = self.get_output_channel_from_channel_id(self.output_1_channel_id)

        if not testing:
            pass
            # import controller-specific modules here

    def run(self):
        try:
            self.logger.info("Activated in {:.1f} ms".format(
                (timeit.default_timer() - self.thread_startup_timer) * 1000))

            self.ready.set()
            self.running = True

            # Make sure the option "Log Level: Debug" is enabled for these
            # messages to appear in the daemon log.
            self.logger.debug(
                "Custom controller started with options: "
                "{}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}".format(
                    self.text_1,
                    self.integer_1,
                    self.float_1,
                    self.bool_1,
                    self.select_1,
                    self.select_measurement_1_device_id,
                    self.select_measurement_1_measurement_id,
                    self.output_1_device_id,
                    self.output_1_measurement_id,
                    self.output_1_channel_id,
                    self.select_device_1_id))

            # Get last measurement for select_measurement_1
            last_measurement = self.get_last_measurement(
                self.select_measurement_1_device_id,
                self.select_measurement_1_measurement_id)

            if last_measurement:
                self.logger.debug(
                    "Most recent timestamp and measurement for "
                    "select_measurement_1: {timestamp}, {meas}".format(
                        timestamp=last_measurement[0],
                        meas=last_measurement[1]))
            else:
                self.logger.debug(
                    "Could not find a measurement in the database for "
                    "select_measurement_1 device ID {} and measurement "
                    "ID {}".format(
                        self.select_measurement_1_device_id,
                        self.select_measurement_1_measurement_id))

            # Turn Output select_device_1 on for 15 seconds
            self.logger.debug("Turning select_device_1 with ID {} on for 15 seconds...".format(
                self.select_device_1_id))
            self.control.output_on(
                self.select_device_1_id,
                output_type='sec',
                output_channel=self.output_1_channel,
                amount=15)

            # Deactivate controller in the SQL database
            self.logger.debug(
                "Deactivating (SQL) Custom controller select_device_2 with ID {}".format(self.select_device_2_id))
            from mycodo.databases.utils import session_scope
            from mycodo.config import SQL_DATABASE_MYCODO
            MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO
            with session_scope(MYCODO_DB_PATH) as new_session:
                mod_cont = new_session.query(CustomController).filter(
                    CustomController.unique_id == self.select_device_2_id).first()
                mod_cont.is_activated = False
                new_session.commit()

            # Deactivate select_device_1_id in the dameon
            # Since we're deactivating this controller (itself), we need to thread this command
            # Note: this command will only deactivate the controller in the Daemon. It will still
            # be activated in the database, so the next restart of the daemon, this controller
            # will start back up again. This is why the previous action deactivated the controller
            # in the database prior to deactivating it in the daemon.
            self.logger.debug(
                "Deactivating (Daemon) Custom controller select_device_2 with"
                " ID {} ...".format(self.select_device_2_id))
            deactivate_controller = threading.Thread(
                target=self.control.controller_deactivate,
                args=(self.select_device_2_id,))
            deactivate_controller.start()

            # Start a loop
            while self.running:
                time.sleep(1)
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
        pass

    def initialize_variables(self):
        controller = db_retrieve_table_daemon(
            CustomController, unique_id=self.unique_id)
        self.log_level_debug = controller.log_level_debug
        self.set_log_level_debug(self.log_level_debug)
