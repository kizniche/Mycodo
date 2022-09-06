# coding=utf-8
#
#  regulate_ph_ec.py - Regulate pH and Electrical Conductivity
#
#  Copyright (C) 2015-2022 Kyle T. Gabriel <mycodo@kylegabriel.com>
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

from flask_babel import lazy_gettext

from mycodo.databases.models import CustomController
from mycodo.databases.models import SMTP
from mycodo.functions.base_function import AbstractFunction
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.constraints_pass import constraints_pass_positive_value
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.send_data import send_email

measurements_dict = {0: {}}

FUNCTION_INFORMATION = {
    'function_name_unique': 'REGULATE_PH_EC',
    'function_name': 'Regulate pH and Electrical Conductivity',
    'measurements_dict': measurements_dict,
    'enable_channel_unit_select': False,

    'message': 'This function regulates pH with 2 pumps (acid and base solutions) and electrical conductivity (EC) with up to 4 pumps (nutrient solutions A, B, C, and D). Set only the nutrient solution outputs you want to use. Any outputs not set will not dispense when EC is being adjusted, allowing as few as 1 pump or as many as 4 pumps. Outputs can be instructed to turn on for durations (seconds) or volumes (ml). Set each Output Type to the correct type for each selected Output Channel (only select on/off Output Channels for durations and volume Output Channels for volumes). If an e-mail address (or multiple addresses separated by commas) is entered into the E-Mail Notification field, a notification e-mail will be sent if 1) pH is outside the set danger range, 2) EC is too high and water needs to be added to the reservoir, or 3) a measurement could not be found in the database for the specific Max Age. Each e-mail notification type has its own timer that prevents e-mail spam, and will only allow sending for each notification type every set E-Mail Timer Duration. After this duration, the timer will automatically reset to allow new notifications to be sent. You may also manually reset e-mail timers at any time with the Custom Commands, below.',

    'options_enabled': ['custom_options'],
    'options_disabled': ['measurements_select'],

    'custom_commands': [
        {
            'type': 'message',
            'default_value': """Each e-mail notification timer can be manually reset before the expiration."""
        },
        {
            'id': 'reset_timer_ec',
            'type': 'button',
            'wait_for_return': True,
            'name': 'Reset EC E-mail Timer'
        },
        {
            'id': 'reset_timer_ph',
            'type': 'button',
            'wait_for_return': True,
            'name': 'Reset pH E-mail Timer'
        },
        {
            'id': 'reset_timer_no_measure',
            'type': 'button',
            'wait_for_return': True,
            'name': 'Reset Measurement Issue E-mail Timer'
        },
        {
            'id': 'reset_timer_all',
            'type': 'button',
            'wait_for_return': True,
            'name': 'Reset All E-Mail Timers'
        }
    ],

    'custom_options': [
        {
            'id': 'period',
            'type': 'float',
            'default_value': 300,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': lazy_gettext('Period (seconds)'),
            'phrase': lazy_gettext('The duration (seconds) between measurements or actions')
        },
        {
            'id': 'start_offset',
            'type': 'integer',
            'default_value': 10,
            'required': True,
            'name': 'Start Offset',
            'phrase': 'The duration (seconds) to wait before the first operation'
        },
        {
            'id': 'period_status',
            'type': 'integer',
            'default_value': 60,
            'required': True,
            'name': 'Status Period (seconds)',
            'phrase': 'The duration (seconds) to update the Function status on the UI'
        },
        {
            'type': 'message',
            'default_value': "Measurement Options"
        },
        {
            'id': 'select_measurement_ph',
            'type': 'select_measurement',
            'default_value': '',
            'options_select': [
                'Input',
                'Function'
            ],
            'name': 'pH Measurement',
            'phrase': 'Measurement from the pH input'
        },
        {
            'id': 'measurement_max_age_ph',
            'type': 'integer',
            'default_value': 360,
            'required': True,
            'name': f"pH {lazy_gettext('Max Age')}",
            'phrase': lazy_gettext('The maximum age (seconds) of the measurement to use')
        },
        {
            'type': 'new_line'
        },
        {
            'id': 'select_measurement_ec',
            'type': 'select_measurement',
            'default_value': '',
            'options_select': [
                'Input',
                'Function'
            ],
            'name': 'EC Measurement',
            'phrase': 'Measurement from the EC input'
        },
        {
            'id': 'measurement_max_age_ec',
            'type': 'integer',
            'default_value': 360,
            'required': True,
            'name': f"EC {lazy_gettext('Max Age')}",
            'phrase': lazy_gettext('The maximum age (seconds) of the measurement to use')
        },
        {
            'type': 'message',
            'default_value': "Output Options"
        },
        {
            'id': 'output_ph_raise',
            'type': 'select_channel',
            'default_value': '',
            'required': True,
            'options_select': [
                'Output_Channels'
            ],
            'name': 'Output: pH Dose Raise (Base)',
            'phrase': 'Select an output to raise the pH'
        },
        {
            'id': 'output_ph_lower',
            'type': 'select_channel',
            'default_value': '',
            'required': True,
            'options_select': [
                'Output_Channels'
            ],
            'name': 'Output: pH Dose Lower (Acid)',
            'phrase': 'Select an output to lower the pH'
        },
        {
            'id': 'output_ph_type',
            'type': 'select',
            'default_value': 'duration_sec',
            'required': True,
            'options_select': [
                ('duration_sec', 'Duration (seconds)'),
                ('volume_ml', 'Volume (ml)')
            ],
            'name': 'pH Output Type',
            'phrase': 'Select the output type for the selected Output Channel'
        },
        {
            'id': 'output_ph_amount',
            'type': 'float',
            'default_value': 2.0,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'pH Output Amount',
            'phrase': 'The amount to send to the pH dosing pumps (duration or volume)'
        },
        {
            'type': 'new_line'
        },
        {
            'id': 'output_ec_a',
            'type': 'select_channel',
            'default_value': '',
            'required': True,
            'options_select': [
                'Output_Channels'
            ],
            'name': 'Output: EC Dose Nutrient A',
            'phrase': 'Select an output to dose nutrient A'
        },
        {
            'id': 'output_ec_a_type',
            'type': 'select',
            'default_value': 'duration_sec',
            'required': True,
            'options_select': [
                ('duration_sec', 'Duration (seconds)'),
                ('volume_ml', 'Volume (ml)')
            ],
            'name': 'Nutrient A Output Type',
            'phrase': 'Select the output type for the selected Output Channel'
        },
        {
            'id': 'output_ec_a_amount',
            'type': 'float',
            'default_value': 2.0,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Nutrient A Output Amount',
            'phrase': 'The amount to send to the Nutrient A dosing pump (duration or volume)'
        },
        {
            'type': 'new_line'
        },
        {
            'id': 'output_ec_b',
            'type': 'select_channel',
            'default_value': '',
            'required': True,
            'options_select': [
                'Output_Channels'
            ],
            'name': 'Output: EC Dose Nutrient B',
            'phrase': 'Select an output to dose nutrient B'
        },
        {
            'id': 'output_ec_b_type',
            'type': 'select',
            'default_value': 'duration_sec',
            'required': True,
            'options_select': [
                ('duration_sec', 'Duration (seconds)'),
                ('volume_ml', 'Volume (ml)')
            ],
            'name': 'Nutrient B Output Type',
            'phrase': 'Select the output type for the selected Output Channel'
        },
        {
            'id': 'output_ec_b_amount',
            'type': 'float',
            'default_value': 2.0,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Nutrient B Output Amount',
            'phrase': 'The amount to send to the Nutrient B dosing pump (duration or volume)'
        },
        {
            'type': 'new_line'
        },
        {
            'id': 'output_ec_c',
            'type': 'select_channel',
            'default_value': '',
            'required': True,
            'options_select': [
                'Output_Channels'
            ],
            'name': 'Output: EC Dose Nutrient C',
            'phrase': 'Select an output to dose nutrient C'
        },
        {
            'id': 'output_ec_c_type',
            'type': 'select',
            'default_value': 'duration_sec',
            'required': True,
            'options_select': [
                ('duration_sec', 'Duration (seconds)'),
                ('volume_ml', 'Volume (ml)')
            ],
            'name': 'Nutrient C Output Type',
            'phrase': 'Select the output type for the selected Output Channel'
        },
        {
            'id': 'output_ec_c_amount',
            'type': 'float',
            'default_value': 2.0,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Nutrient C Output Amount',
            'phrase': 'The amount to send to the Nutrient C dosing pump (duration or volume)'
        },
        {
            'type': 'new_line'
        },
        {
            'id': 'output_ec_d',
            'type': 'select_channel',
            'default_value': '',
            'required': True,
            'options_select': [
                'Output_Channels'
            ],
            'name': 'Output: EC Dose Nutrient D',
            'phrase': 'Select an output to dose nutrient D'
        },
        {
            'id': 'output_ec_d_type',
            'type': 'select',
            'default_value': 'duration_sec',
            'required': True,
            'options_select': [
                ('duration_sec', 'Duration (seconds)'),
                ('volume_ml', 'Volume (ml)')
            ],
            'name': 'Nutrient D Output Type',
            'phrase': 'Select the output type for the selected Output Channel'
        },
        {
            'id': 'output_ec_d_amount',
            'type': 'float',
            'default_value': 2.0,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Nutrient D Output Amount',
            'phrase': 'The amount to send to the Nutrient D dosing pump (duration or volume)'
        },
        {
            'type': 'message',
            'default_value': "Setpoint Options"
        },
        {
            'id': 'setpoint_ph',
            'type': 'float',
            'default_value': 5.85,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'pH Setpoint',
            'phrase': 'The desired pH setpoint'
        },
        {
            'id': 'hysteresis_ph',
            'type': 'float',
            'default_value': 0.35,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'pH Hysteresis',
            'phrase': 'The hysteresis to determine the pH range'
        },
        {
            'type': 'new_line'
        },
        {
            'id': 'setpoint_ec',
            'type': 'float',
            'default_value': 150.0,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'EC Setpoint',
            'phrase': 'The desired electrical conductivity setpoint'
        },
        {
            'id': 'hysteresis_ec',
            'type': 'float',
            'default_value': 50.0,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'EC Hysteresis',
            'phrase': 'The hysteresis to determine the EC range'
        },
        {
            'type': 'new_line'
        },
        {
            'id': 'danger_range_ph_high',
            'type': 'float',
            'default_value': 7.0,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'pH Danger Range (High Value)',
            'phrase': 'This high pH value for the danger range'
        },
        {
            'id': 'danger_range_ph_low',
            'type': 'float',
            'default_value': 5.0,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'pH Danger Range (Low Value)',
            'phrase': 'This low pH value for the danger range'
        },
        {
            'type': 'message',
            'default_value': "Alert Notification Options"
        },
        {
            'id': 'email_notification',
            'type': 'text',
            'default_value': '',
            'required': True,
            'name': 'Notification E-Mail',
            'phrase': 'E-mail to notify when there is an issue (blank to disable)'
        },
        {
            'id': 'email_timer_duration_hours',
            'type': 'float',
            'default_value': 12.0,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'E-Mail Timer Duration (Hours)',
            'phrase': 'How long to wait between sending e-mail notifications'
        }
    ]
}


class CustomModule(AbstractFunction):
    """
    Class to operate custom controller
    """

    def __init__(self, function, testing=False):
        super().__init__(function, testing=testing, name=__name__)

        self.timer_loop = time.time()

        self.control = DaemonControl()

        # Initialize custom options
        self.period = None
        self.select_measurement_ph_device_id = None
        self.select_measurement_ph_measurement_id = None
        self.measurement_max_age_ph = None
        self.select_measurement_ec_device_id = None
        self.select_measurement_ec_measurement_id = None
        self.measurement_max_age_ec = None

        self.output_ph_raise_device_id = None
        self.output_ph_raise_channel_id = None
        self.output_ph_lower_device_id = None
        self.output_ph_lower_channel_id = None
        self.output_ph_type = None
        self.output_ph_amount = None

        self.output_ec_a_device_id = None
        self.output_ec_a_channel_id = None
        self.output_ec_a_type = None
        self.output_ec_a_amount = None

        self.output_ec_b_device_id = None
        self.output_ec_b_channel_id = None
        self.output_ec_b_type = None
        self.output_ec_b_amount = None

        self.output_ec_c_device_id = None
        self.output_ec_c_channel_id = None
        self.output_ec_c_type = None
        self.output_ec_c_amount = None

        self.output_ec_d_device_id = None
        self.output_ec_d_channel_id = None
        self.output_ec_d_type = None
        self.output_ec_d_amount = None

        self.setpoint_ph = None
        self.hysteresis_ph = None
        self.setpoint_ec = None
        self.hysteresis_ec = None
        self.danger_range_ph_high = None
        self.danger_range_ph_low = None

        self.email_notification = None
        self.email_timer_duration_hours = None

        self.range_ph = None
        self.range_ec = None
        self.ph_type = None

        self.output_ph_raise_channel = None
        self.output_ph_lower_channel = None

        self.output_ec_a_channel = None
        self.output_ec_b_channel = None
        self.output_ec_c_channel = None
        self.output_ec_d_channel = None

        self.email_timers = {
            "notify_ec": 0,
            "notify_ph": 0,
            "notify_none": 0
        }

        self.output_types = {
            'duration_sec': 'sec',
            'volume_ml': 'ml'
        }

        self.list_doses = []
        self.ratio_letters = []
        self.ratio_numbers = []

        # Set custom options
        custom_function = db_retrieve_table_daemon(
            CustomController, unique_id=self.unique_id)
        self.setup_custom_options(
            FUNCTION_INFORMATION['custom_options'], custom_function)

        if not testing:
            self.try_initialize()

    def initialize(self):
        self.timer_loop = time.time() + self.start_offset

        self.range_ph = (self.setpoint_ph - self.hysteresis_ph, self.setpoint_ph + self.hysteresis_ph)
        self.range_ec = (self.setpoint_ec - self.hysteresis_ec, self.setpoint_ec + self.hysteresis_ec)

        self.output_ph_raise_channel = self.get_output_channel_from_channel_id(
            self.output_ph_raise_channel_id)
        self.output_ph_lower_channel = self.get_output_channel_from_channel_id(
            self.output_ph_lower_channel_id)

        self.output_ec_a_channel = self.get_output_channel_from_channel_id(
            self.output_ec_a_channel_id)
        self.output_ec_b_channel = self.get_output_channel_from_channel_id(
            self.output_ec_b_channel_id)
        self.output_ec_c_channel = self.get_output_channel_from_channel_id(
            self.output_ec_c_channel_id)
        self.output_ec_d_channel = self.get_output_channel_from_channel_id(
            self.output_ec_d_channel_id)

        self.ph_type = 'sec'
        if self.output_ph_type == "volume_ml":
            self.ph_type = 'vol'

        self.ec_a_type = 'sec'
        if self.output_ec_a_type == "volume_ml":
            self.ec_a_type = 'vol'

        self.ec_b_type = 'sec'
        if self.output_ec_b_type == "volume_ml":
            self.ec_b_type = 'vol'

        self.ec_c_type = 'sec'
        if self.output_ec_c_type == "volume_ml":
            self.ec_c_type = 'vol'

        self.ec_d_type = 'sec'
        if self.output_ec_d_type == "volume_ml":
            self.ec_d_type = 'vol'

        if "," in self.email_notification:
            self.email_notification = self.email_notification.split(",")

        if self.output_ec_a_device_id:
            self.ratio_letters.append("A")
            self.ratio_numbers.append(self.output_ec_a_amount)
            self.list_doses.append(f"{self.output_ec_a_amount} {self.output_types[self.output_ec_a_type]} Nut A")
        if self.output_ec_b_device_id:
            self.ratio_letters.append("B")
            self.ratio_numbers.append(self.output_ec_b_amount)
            self.list_doses.append(f"{self.output_ec_b_amount} {self.output_types[self.output_ec_b_type]} Nut B")
        if self.output_ec_c_device_id:
            self.ratio_letters.append("C")
            self.ratio_numbers.append(self.output_ec_c_amount)
            self.list_doses.append(f"{self.output_ec_c_amount} {self.output_types[self.output_ec_c_type]} Nut C")
        if self.output_ec_d_device_id:
            self.ratio_letters.append("D")
            self.ratio_numbers.append(self.output_ec_d_amount)
            self.list_doses.append(f"{self.output_ec_d_amount} {self.output_types[self.output_ec_d_type]} Nut D")

    def loop(self):
        if self.timer_loop > time.time():
            return

        while self.timer_loop < time.time():
            self.timer_loop += self.period

        message = ""

        # Get last measurement for pH
        last_measurement_ph = self.get_last_measurement(
            self.select_measurement_ph_device_id,
            self.select_measurement_ph_measurement_id,
            max_age=self.measurement_max_age_ph)

        if last_measurement_ph:
            self.logger.debug(
                "Most recent timestamp and measurement for "
                f"pH: {last_measurement_ph[0]}, {last_measurement_ph[1]}")
        else:
            self.logger.error(
                "Could not find a measurement in the database for "
                f"Measurement A device ID {self.select_measurement_ph_device_id} and measurement "
                f"ID {self.select_measurement_ph_measurement_id} in the past {self.measurement_max_age_ph} seconds")

        # Get last measurement for EC
        last_measurement_ec = self.get_last_measurement(
            self.select_measurement_ec_device_id,
            self.select_measurement_ec_measurement_id,
            max_age=self.measurement_max_age_ec)

        if last_measurement_ec:
            self.logger.debug(
                "Most recent timestamp and measurement for "
                f"EC: {last_measurement_ec[0]}, {last_measurement_ec[1]}")
        else:
            self.logger.error(
                "Could not find a measurement in the database for "
                f"Measurement A device ID {self.select_measurement_ec_device_id} and measurement "
                f"ID {self.select_measurement_ec_measurement_id} in the past {self.measurement_max_age_ec} seconds")

        self.logger.debug(f"Measurements: EC: {last_measurement_ec[1]}, pH: {last_measurement_ph[1]}")

        if None in [last_measurement_ec[1], last_measurement_ph[1]]:
            if last_measurement_ec[1] is None:
                message += "\nWarning: No EC Measurement! Check sensor!"
            if last_measurement_ph[1] is None:
                message += "\nWarning: No pH Measurement! Check sensor!"

            if self.email_notification:
                if self.email_timers['notify_none'] < time.time():
                    self.email_timers['notify_none'] = time.time() + (self.email_timer_duration_hours * 60 * 60)
                    self.email(message)
            return

        #
        # First check if pH is dangerously low or high, and adjust if it is
        #

        # pH dangerously low, add base (pH up)
        if last_measurement_ph[1] < self.danger_range_ph_low:
            msg = f"pH is dangerously low: {last_measurement_ph[1]}. Should be > {self.danger_range_ph_low}. " \
                  f"Dispensing {self.output_ph_amount} {self.output_types[self.output_ph_type]} base"
            self.logger.debug(msg)
            message += msg

            output_on_off = threading.Thread(
                target=self.control.output_on_off,
                args=(self.output_ph_raise_device_id, "on",),
                kwargs={'output_type': self.ph_type,
                        'amount': self.output_ph_amount,
                        'output_channel': self.output_ph_raise_channel})
            output_on_off.start()

            if self.email_notification:
                if self.email_timers['notify_ph'] < time.time():
                    self.email_timers['notify_ph'] = time.time() + (self.email_timer_duration_hours * 60 * 60)
                    self.email(message)

        # pH dangerously high, add acid (pH down)
        elif last_measurement_ph[1] > self.danger_range_ph_high:
            msg = f"pH is dangerously high: {last_measurement_ph[1]}. Should be < {self.danger_range_ph_high}. " \
                  f"Dispensing {self.output_ph_amount} {self.output_types[self.output_ph_type]} acid"
            self.logger.debug(msg)
            message += msg

            output_on_off = threading.Thread(
                target=self.control.output_on_off,
                args=(self.output_ph_lower_device_id, "on",),
                kwargs={'output_type': self.ph_type,
                        'amount': self.output_ph_amount,
                        'output_channel': self.output_ph_lower_channel})
            output_on_off.start()

            if self.email_notification:
                if self.email_timers['notify_ph'] < time.time():
                    self.email_timers['notify_ph'] = time.time() + (self.email_timer_duration_hours * 60 * 60)
                    self.email(message)

        #
        # If pH isn't dangerously low or high, check if EC is within range
        #

        # EC too low, add nutrient
        elif last_measurement_ec[1] < self.range_ec[0]:
            self.logger.debug(
                f"EC: {last_measurement_ec[1]}. Should be > {self.range_ec[0]}. "
                f"Dosing {':'.join(self.ratio_numbers)} ({':'.join(map(str, self.ratio_letters))}): {', '.join(self.list_doses)})")

            if self.output_ec_a_device_id:
                output_on_off = threading.Thread(
                    target=self.control.output_on_off,
                    args=(self.output_ec_a_device_id, "on",),
                    kwargs={'output_type': self.ec_a_type,
                            'amount': self.output_ec_a_amount,
                            'output_channel': self.output_ec_a_channel})
                output_on_off.start()

            if self.output_ec_b_device_id:
                output_on_off = threading.Thread(
                    target=self.control.output_on_off,
                    args=(self.output_ec_b_device_id, "on",),
                    kwargs={'output_type': self.ec_b_type,
                            'amount': self.output_ec_b_amount,
                            'output_channel': self.output_ec_b_channel})
                output_on_off.start()

            if self.output_ec_c_device_id:
                output_on_off = threading.Thread(
                    target=self.control.output_on_off,
                    args=(self.output_ec_c_device_id, "on",),
                    kwargs={'output_type': self.ec_c_type,
                            'amount': self.output_ec_c_amount,
                            'output_channel': self.output_ec_c_channel})
                output_on_off.start()

            if self.output_ec_d_device_id:
                output_on_off = threading.Thread(
                    target=self.control.output_on_off,
                    args=(self.output_ec_d_device_id, "on",),
                    kwargs={'output_type': self.ec_d_type,
                            'amount': self.output_ec_d_amount,
                            'output_channel': self.output_ec_d_channel})
                output_on_off.start()

        # EC too high, add nutrient
        elif last_measurement_ec[1] > self.range_ec[1]:
            msg = f"EC: {last_measurement_ec[1]}. Should be < {self.range_ec[1]}. Need to add water to dilute!"
            self.logger.debug(msg)

            if self.email_notification:
                if self.email_timers['notify_ec'] < time.time():
                    self.email_timers['notify_ec'] = time.time() + (self.email_timer_duration_hours * 60 * 60)
                    message += msg
                    self.email(message)

        #
        # If pH is in range, make sure pH is within range
        #

        # pH too low, add base (pH up)
        elif last_measurement_ph[1] < self.range_ph[0]:
            self.logger.debug(
                f"pH is {last_measurement_ph[1]}. Should be > {self.range_ph[0]}. "
                f"Dispensing {self.output_ph_amount} {self.output_types[self.output_ph_type]} base")

            output_on_off = threading.Thread(
                target=self.control.output_on_off,
                args=(self.output_ph_raise_device_id, "on",),
                kwargs={'output_type': self.ph_type,
                        'amount': self.output_ph_amount,
                        'output_channel': self.output_ph_raise_channel})
            output_on_off.start()

        # pH too high, add acid (pH down)
        elif last_measurement_ph[1] > self.range_ph[1]:
            self.logger.debug(
                f"pH is {last_measurement_ph[1]}. Should be < {self.range_ph[1]}. "
                f"Dispensing {self.output_ph_amount} {self.output_types[self.output_ph_type]} acid")

            output_on_off = threading.Thread(
                target=self.control.output_on_off,
                args=(self.output_ph_lower_device_id, "on",),
                kwargs={'output_type': self.ph_type,
                        'amount': self.output_ph_amount,
                        'output_channel': self.output_ph_lower_channel})
            output_on_off.start()

    def email(self, message):
        smtp = db_retrieve_table_daemon(SMTP, entry='first')
        send_email(smtp.host, smtp.protocol, smtp.port,
                   smtp.user, smtp.passw, smtp.email_from,
                   self.email_notification, message)

    def reset_timer_ec(self, args_dict):
        self.email_timers['notify_ec'] = 0

    def reset_timer_ph(self, args_dict):
        self.email_timers['notify_ph'] = 0

    def reset_timer_no_measure(self, args_dict):
        self.email_timers['notify_none'] = 0

    def reset_timer_all(self, args_dict):
        self.email_timers['notify_ec'] = 0
        self.email_timers['notify_ph'] = 0
        self.email_timers['notify_none'] = 0

    def function_status(self):
        return_str = {
            'string_status': f"Regulating"
                             f"<br>pH: {self.range_ph[0]:.2f} - {self.range_ph[1]:.2f} at {self.output_ph_amount:.2f} {self.output_types[self.output_ph_type]}"
                             f"<br>EC: {self.range_ec[0]:.2f} - {self.range_ec[1]:.2f} at {':'.join(map(str, self.ratio_numbers))} ({':'.join(self.ratio_letters)})",
            'error': []
        }
        self.logger.info(f"TEST00: {return_str}")
        return return_str
