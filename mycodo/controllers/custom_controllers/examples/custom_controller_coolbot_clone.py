# coding=utf-8
#
#  custom_controller_coolbot_clone.py - Custom controller coolbot clone
#
#  Copyright (C) 2017  Kyle T. Gabriel
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


CONTROLLER_INFORMATION = {
    'controller_name_unique': 'COOLBOT_CLONE',
    'controller_name': 'CoolBot Clone',

    'message': 'This controller is a CoolBot cone, which will provide the functionality of a CoolBot. '
               'Requirements: Output to control the AC unit, output to power the heating unit attached '
               'to the AC temperature sensor (disconnected from the AC airway), and a temperature sensor '
               'attached to the condenser to detect freezing.',

    'options_enabled': [
        'custom_options'
    ],

    'dependencies_module': [],

    'custom_options': [
        {
            'id': 'start_offset',
            'type': 'integer',
            'default_value': 30,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': lazy_gettext('Start Offset (seconds)'),
            'phrase': lazy_gettext('Wait before starting the controller')
        },
        {
            'id': 'period',
            'type': 'integer',
            'default_value': 120,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': lazy_gettext('Period (seconds)'),
            'phrase': lazy_gettext('How often to check the temperature and adjust AC')
        },
        {
            'id': 'input_temperature_condenser',
            'type': 'select_measurement',
            'default_value': '',
            'options_select': [
                'Input',
                'Math'
            ],
            'name': lazy_gettext('Input: Condenser Temperature'),
            'phrase': lazy_gettext('The temperature sensor attached to the AC condenser')
        },
        {
            'id': 'input_temperature_condenser_max_age',
            'type': 'integer',
            'default_value': 120,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': lazy_gettext('Condenser Temperature Max Age (seconds)'),
            'phrase': lazy_gettext('The maximum allowed age of the condenser temperature measurement. '
                                   'If older than this value, the system shuts down.')
        },
        {
            'id': 'input_temperature_room',
            'type': 'select_measurement',
            'default_value': '',
            'options_select': [
                'Input',
                'Math'
            ],
            'name': lazy_gettext('Input: Room Temperature'),
            'phrase': lazy_gettext('The temperature sensor measuring the temperature in the room')
        },
        {
            'id': 'input_temperature_room_max_age',
            'type': 'integer',
            'default_value': 120,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': lazy_gettext('Room Temperature Max Age (seconds)'),
            'phrase': lazy_gettext('The maximum allowed age of the room temperature measurement. '
                                   'If older than this value, the system shuts down.')
        },
        {
            'id': 'output_ac',
            'type': 'select_device',
            'default_value': '',
            'options_select': [
                'Output',
            ],
            'name': lazy_gettext('Output: AC'),
            'phrase': lazy_gettext('The output the controls power to the AC')
        },
        {
            'id': 'output_ac_sensor_heater',
            'type': 'select_device',
            'default_value': '',
            'options_select': [
                'Output',
            ],
            'name': lazy_gettext('Output: Heater'),
            'phrase': lazy_gettext('The output that heats the AC temperature sensor')
        },
        {
            'id': 'setpoint_temperature',
            'type': 'float',
            'default_value': 10.5,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': lazy_gettext('Temperature Setpoint'),
            'phrase': lazy_gettext('The desired temperature')
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
        self.start_offset = None
        self.period = None
        self.input_temperature_condenser_device_id = None
        self.input_temperature_condenser_measurement_id = None
        self.input_temperature_condenser_max_age = None
        self.input_temperature_room_device_id = None
        self.input_temperature_room_measurement_id = None
        self.input_temperature_room_max_age = None
        self.output_ac_id = None
        self.output_ac_sensor_heater_id = None
        self.setpoint_temperature = None

        # Set custom options
        custom_controller = db_retrieve_table_daemon(
            CustomController, unique_id=unique_id)
        self.setup_custom_options(
            CONTROLLER_INFORMATION['custom_options'], custom_controller)

        if not testing:
            pass
            # import controller-specific modules here

    def get_ac_condenser_temperature(self):
        """Get condenser temperature"""
        last_measurement = self.get_last_measurement(
            self.input_temperature_condenser_device_id,
            self.input_temperature_condenser_measurement_id,
            max_age=self.input_temperature_condenser_max_age)

        if last_measurement:
            self.logger.debug(
                "Most recent timestamp and measurement for "
                "input_temperature_condenser: {timestamp}, {meas}".format(
                    timestamp=last_measurement[0],
                    meas=last_measurement[1]))
            return last_measurement
        else:
            self.logger.debug(
                "Could not find a measurement in the database for "
                "input_temperature_condenser device ID {} and measurement "
                "ID {}".format(
                    self.input_temperature_condenser_device_id,
                    self.input_temperature_condenser_measurement_id))

    def get_room_temperature(self):
        """Get condenser temperature"""
        last_measurement = self.get_last_measurement(
            self.input_temperature_room_device_id,
            self.input_temperature_room_measurement_id,
            max_age=self.input_temperature_room_max_age)

        if last_measurement:
            self.logger.debug(
                "Most recent timestamp and measurement for "
                "input_temperature_room: {timestamp}, {meas}".format(
                    timestamp=last_measurement[0],
                    meas=last_measurement[1]))
            return last_measurement
        else:
            self.logger.debug(
                "Could not find a measurement in the database for "
                "input_temperature_room device ID {} and measurement "
                "ID {}".format(
                    self.input_temperature_room_device_id,
                    self.input_temperature_room_measurement_id))

    def run(self):
        try:
            self.logger.info("Activated in {:.1f} ms".format(
                (timeit.default_timer() - self.thread_startup_timer) * 1000))

            self.ready.set()
            self.running = True

            start_offset_timer = time.time() + self.start_offset
            while self.running and time.time() < start_offset_timer:
                time.sleep(1)
            if not self.running:
                return

            # try to get measurement from sensor
            temperature_condenser = self.get_ac_condenser_temperature()
            temperature_room = self.get_room_temperature()
            if not temperature_condenser or not temperature_room:
                return

            # Turn Output output_ac on
            self.logger.debug(
                "Turning output_ac with ID {} on".format(self.output_ac_id))
            self.control.output_on(self.output_ac_id)

            # Start a loop
            while self.running:
                temperature_condenser = self.get_ac_condenser_temperature()
                temperature_room = self.get_room_temperature()

                if temperature_room > self.setpoint_temperature and temperature_condenser > 0:
                    # Turn Output output_ac_sensor_heater on
                    self.logger.debug(
                        "Turning output_ac_sensor_heater with ID {} on".format(
                            self.output_ac_sensor_heater_id))
                    self.control.output_on(self.output_ac_sensor_heater_id)
                else:
                    # Turn Output output_ac_sensor_heater off
                    self.logger.debug(
                        "Turning output_ac_sensor_heater with ID {} off".format(
                            self.output_ac_sensor_heater_id))
                    self.control.output_off(self.output_ac_sensor_heater_id)

                time.sleep(self.period)
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

    def run_finally(self):
        # Turn Output output_ac off
        self.logger.debug(
            "Turning output_ac with ID {} off".format(self.output_ac_id))
        self.control.output_off(self.output_ac_id)

        # Turn Output output_ac_sensor_heater off
        self.logger.debug(
            "Turning output_ac_sensor_heater with ID {} off".format(
                self.output_ac_sensor_heater_id))
        self.control.output_off(self.output_ac_sensor_heater_id)
