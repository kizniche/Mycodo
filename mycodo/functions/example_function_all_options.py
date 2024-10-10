# coding=utf-8
#
#  example_function_all_options.py - Example function module with all options
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
import datetime
import threading
import time

from flask_babel import lazy_gettext

from mycodo.databases.models import CustomController
from mycodo.functions.base_function import AbstractFunction
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.constraints_pass import constraints_pass_positive_value
from mycodo.utils.database import db_retrieve_table_daemon

FUNCTION_INFORMATION = {
    'function_name_unique': 'example_function_generic',
    'function_name': 'Example: Generic',

    'message': 'This is an example Function Module that showcases all the different type of UI options. '
               'It is not useful beyond showing how to develop new custom Function modules.'
               'This message will appear above the Function options. '
               'It will retrieve the last selected measurement, turn the selected output '
               'on for 15 seconds, then deactivate itself. Study the code to develop your '
               'own Function Module that can be imported on the Function Import page.',

    'options_enabled': [
        'custom_options',
        'function_status'
    ],

    'dependencies_module': [
        # Example dependencies that will be installed when the user adds the controller
        ('apt', 'build-essential', 'build-essential'),
        # ('apt', 'bison', 'bison'),
        # ('apt', 'libasound2-dev', 'libasound2-dev'),
        # ('apt', 'libpulse-dev', 'libpulse-dev'),
        # ('apt', 'swig', 'swig'),
        # ('pip-pypi', 'pocketsphinx', 'pocketsphinx==0.1.17')
        # Note: specify the pip-pypi package version, but also search for this same package
        # used elsewhere in Mycodo. All need to be set to the same version in order to prevent conflicts.
    ],

    # These options will appear in the settings of the Function,
    # which the user can use to set different values and options for the Function.
    # These settings can only be changed when the Function is inactive.
    'custom_options': [
        {
            'id': 'period',
            'type': 'float',
            'default_value': 60,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': "{} ({})".format(lazy_gettext('Period'), lazy_gettext('Seconds')),
            'phrase': lazy_gettext('The duration between measurements or actions')
        },
        {
            'type': 'message',
            'default_value': """The following fields are for text, integers, and decimal inputs. This message will automatically create a new line for the options that come after it. Alternatively, a new line can be created instead without a message, which are what separates each of the following three inputs."""
        },
        {
            'id': 'text_1',
            'type': 'text',
            'default_value': 'Text_1',
            'required': True,
            'name': 'Text Input',
            'phrase': 'Type in text'
        },
        {
            'type': 'new_line'
        },
        {
            'id': 'integer_1',
            'type': 'integer',
            'default_value': 100,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Integer Input',
            'phrase': 'Type in an Integer'
        },
        {
            'type': 'new_line'
        },
        {
            'id': 'float_1',
            'type': 'float',
            'default_value': 50.2,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Devimal Input',
            'phrase': 'Type in a decimal value'
        },
        {
            'type': 'message',
            'default_value': """A boolean value can be made using a checkbox."""
        },
        {
            'id': 'bool_1',
            'type': 'bool',
            'default_value': True,
            'name': 'Boolean Value',
            'phrase': 'Set to either True (checked) or False (Unchecked)'
        },
        {
            'type': 'message',
            'default_value': """A dropdown selection can be made of any user-defined options, with any of the options selected by default when the Function is added by the user."""
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
            'name': 'Select Option',
            'phrase': 'Select an option from the dropdown'
        },
        {
            'type': 'message',
            'default_value': """A specific measurement from an Input, Function, or PID Controller can be selected. The following dropdown will be populated if at least one Input, Function, or PID Controller has been created (as long as the Function has measurements, e.g. Statistics Function)."""
        },
        {
            'id': 'select_measurement_1',
            'type': 'select_measurement',
            'default_value': '',
            'options_select': [
                'Input',
                'Function',
                'PID'
            ],
            'name': 'Controller Measurement',
            'phrase': 'Select a controller Measurement'
        },
        {
            'type': 'message',
            'default_value': """An output channel measurement can be selected that will return the Output ID, Channel ID, and Measurement ID. This is useful if you need more than just the Output and Channel IDs and require the user to select the specific Measurement of a channel."""
        },
        {
            'id': 'output_1',
            'type': 'select_measurement_channel',
            'default_value': '',
            'required': True,
            'options_select': [
                'Output_Channels_Measurements',
            ],
            'name': 'Output Channel Measurement',
            'phrase': 'Select an output channel and measurement '
        },
        {
            'type': 'message',
            'default_value': """An output can be selected that will return the Output ID if only the output ID is needed."""
        },
        {
            'id': 'select_device_1',
            'type': 'select_device',
            'default_value': '',
            'options_select': [
                'Output',
            ],
            'name': 'Output Device',
            'phrase': 'Select an Output device'
        },
        {
            'type': 'message',
            'default_value': """An Input, Output, Function, PID, or Trigger can be selected that will return the ID if only the controller ID is needed (e.g. for activating/deactivating a controller)"""
        },
        {
            'id': 'select_device_2',
            'type': 'select_device',
            'default_value': '',
            'options_select': [
                'Input',
                'Output',
                'Function',
                'PID',
                'Trigger'
            ],
            'name': 'Controller Device',
            'phrase': 'Select an Input/Output/Function/PID/Trigger controller'
        }
    ],

    # Custom Actions give the user the ability to interact with the running Function Controller.
    # Each button will execute a different function within the Function Controller and pass any
    # input (text, numbers, selections, etc.) the user entered. This is useful for such things as
    # calibration.
    'custom_commands_message': 'This is a message for custom actions that will appear above all actions.',
    'custom_commands': [
        {
            'type': 'message',
            'default_value': 'Button One will pass the Button One Value to the button_one() function of this module. This allows functions to be executed with user-specified inputs. These can be text, integers, decimals, or boolean values.',
        },
        {
            'id': 'button_one_value',
            'type': 'integer',
            'default_value': 650,
            'name': 'Button One Value',
            'phrase': 'Value for button one.'
        },
        {
            'id': 'button_one',  # This button will execute the "button_one(self, args_dict) function, below
            'type': 'button',
            'wait_for_return': True,  # The UI will wait until the function has returned the UI with a value to display
            'name': 'Button One',
            'phrase': "This is button one"
        },
        {
            'type': 'message',
            'default_value': 'Here is another action with another user input that will be passed to the function. Note that Button One Value will also be passed to this second function, so be sure to use unique ids for each input.',
        },
        {
            'id': 'button_two_value',
            'type': 'integer',
            'default_value': 1500,
            'name': 'Button Two Value',
            'phrase': 'Value for button two.'
        },
        {
            'id': 'button_two',
            'type': 'button',
            'wait_for_return': False,  # Refreshing the UI will not wait for the function to complete
            'name': 'Button Two',
            'phrase': "This is button two"
        }
    ]
}


class CustomModule(AbstractFunction):
    """
    Class to operate custom controller
    """
    def __init__(self, function, testing=False):
        super().__init__(function, testing=testing, name=__name__)

        self.control = DaemonControl()
        self.listener_running = True
        self.timer_loop = time.time()  # start the loop() timer

        #
        # Initialize what you defined in custom_options, above
        #

        self.period = None  # How often to run loop()

        # Standard custom options inherit the name you defined in the "id" key
        self.text_1 = None
        self.integer_1 = None
        self.float_1 = None
        self.bool_1 = None
        self.select_1 = None

        # Custom options of type "select_measurement" require creating two variables and adding "_device_id"
        # and "_measurement_id" after the name
        self.select_measurement_1_device_id = None
        self.select_measurement_1_measurement_id = None

        # Custom options of type "select_measurement_channel" require three variables and adding
        # "device_id", "measurement_id", and "channel_id" after the name
        self.output_1_device_id = None
        self.output_1_measurement_id = None
        self.output_1_channel_id = None

        # Custom options of type "select_device" require adding "_id" after the name
        self.select_device_1_id = None
        self.select_device_2_id = None

        #
        # Set custom options
        #
        custom_function = db_retrieve_table_daemon(
            CustomController, unique_id=self.unique_id)
        self.setup_custom_options(
            FUNCTION_INFORMATION['custom_options'], custom_function)

        # Get selected output channel number
        self.output_1_channel = self.get_output_channel_from_channel_id(
            self.output_1_channel_id)

        if not testing:
            self.try_initialize()

    def initialize(self):
        # import controller-specific modules here
        # You may import something you defined in dependencies_module
        pass

    def loop(self):
        """This will run periodically. Delete this function if you only want to use listener()"""
        if self.timer_loop > time.time():
            return

        while self.timer_loop < time.time():
            self.timer_loop += self.period

        try:
            # This log line will appear in the Daemon log under Config -> Mycodo Logs
            self.logger.info("Function loop() running")

            # Make sure the option "Log Level: Debug" is enabled for these debug
            # log lines to appear in the Daemon log.
            self.logger.debug(
                "Custom controller started with options: "
                "{}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}".format(
                    self.period,
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

            # You can specify different log levels to indicate things such as errors
            self.logger.error("This is an error line that will appear in the log")

            # And Warnings
            self.logger.warning("This is a warning line that will appear in the log")

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
            from mycodo.config import MYCODO_DB_PATH
            from mycodo.databases.utils import session_scope
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
        except:
            self.logger.exception("Run Error")
        finally:
            self.logger.error("Deactivated unexpectedly")

    def listener(self):
        """This function will be turned into a thread. Delete this function if you don't want to use it."""
        while self.listener_running:
            self.logger.info("This process is running in a separate thread from the main loop().")
            time.time(60)

    def button_one(self, args_dict):
        self.logger.error("Button One Pressed!: {}".format(int(args_dict['button_one_value'])))
        return "Here return message will be seen in the web UI. " \
               "This only works when 'wait_for_return' is set True."

    def button_two(self, args_dict):
        self.logger.error("Button Two Pressed!: {}".format(int(args_dict['button_two_value'])))
        return "This message will never be seen in the web UI because this process is threaded"

    def function_status(self):
        return_dict = {
            'string_status': f"Current time: {datetime.datetime.now()} ({time.time()})"
                             f"\ntext: {self.text_1}"
                             f"\ninteger: {self.integer_1}"
                             f"\nfloat: {self.float_1}"
                             f"\nboolean: {self.bool_1}",
            'error': []
        }
        return return_dict
