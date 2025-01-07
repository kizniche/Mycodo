# coding=utf-8
#
#  pid_autotune.py - PID Controller Autotune
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

from flask_babel import lazy_gettext

from mycodo.config import MYCODO_DB_PATH
from mycodo.databases.models import CustomController
from mycodo.databases.utils import session_scope
from mycodo.functions.base_function import AbstractFunction
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.PID_hirschmann.pid_autotune import PIDAutotune
from mycodo.utils.constraints_pass import constraints_pass_positive_value
from mycodo.utils.database import db_retrieve_table_daemon


FUNCTION_INFORMATION = {
    'function_name_unique': 'pid_autotune',
    'function_name': 'PID Autotune',

    'message': 'This function will attempt to perform a PID controller autotune. That is, an output will be powered '
               'and the response measured from a sensor several times to calculate the P, I, and D gains. Updates '
               'about the operation will be sent to the Daemon log. If the autotune successfully completes, a summary '
               'will be sent to the Daemon log as well. Currently, only raising a Measurement is supported, but '
               'lowering should be possible with some modification to the function controller code. It is recommended '
               'to create a graph on a dashboard with the Measurement and Output to monitor that the Output is '
               'successfully raising the Measurement beyond the Setpoint. Note: Autotune is an experimental feature, '
               'it is not well-developed, and it has a high likelihood of failing to generate PID gains. Do not rely '
               'on it for accurately tuning your PID controller.',

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
            'phrase': 'Select an output to modulate that will affect the measurement'
        },
        {
            'id': 'period',
            'type': 'integer',
            'default_value': 30,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': lazy_gettext('Period'),
            'phrase': 'The period between powering the output'
        },
        {
            'id': 'setpoint',
            'type': 'float',
            'default_value': 50,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': lazy_gettext('Setpoint'),
            'phrase': 'A value sufficiently far from the current measured value that the output is capable of pushing the measurement toward'
        },
        {
            'id': 'noiseband',
            'type': 'float',
            'default_value': 0.5,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': lazy_gettext('Noise Band'),
            'phrase': 'The amount above the setpoint the measurement must reach'
        },
        {
            'id': 'outstep',
            'type': 'float',
            'default_value': 10,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': lazy_gettext('Outstep'),
            'phrase': 'How many seconds the output will turn on every Period'
        },
        {
            'type': 'message',
            'default_value': 'Currently, only autotuning to raise a condition (measurement) is supported.',
        },
        {
            'id': 'direction',
            'type': 'select',
            'default_value': 'raise',
            'options_select': [
                ('raise', 'Raise')
            ],
            'name': lazy_gettext('Direction'),
            'phrase': 'The direction the Output will push the Measurement'
        }
    ]
}


class CustomModule(AbstractFunction):
    """
    Class to operate custom controller
    """
    def __init__(self, function, testing=False):
        super().__init__(function, testing=testing, name=__name__)

        self.autotune = None
        self.autotune_active = None
        self.control_variable = None
        self.timestamp = None
        self.timer_loop = None
        self.control = DaemonControl()

        # Initialize custom options
        self.measurement_device_id = None
        self.measurement_measurement_id = None
        self.output_device_id = None
        self.output_measurement_id = None
        self.output_channel_id = None
        self.setpoint = None
        self.period = None
        self.noiseband = None
        self.outstep = None
        self.direction = None

        self.output_channel = None

        # Set custom options
        custom_function = db_retrieve_table_daemon(
            CustomController, unique_id=self.unique_id)
        self.setup_custom_options(
            FUNCTION_INFORMATION['custom_options'], custom_function)

        self.output_channel = self.get_output_channel_from_channel_id(self.output_channel_id)

        if not testing:
            self.try_initialize()

    def initialize(self):
        self.timestamp = time.time()
        self.autotune = PIDAutotune(
            self.setpoint,
            out_step=self.outstep,
            sampletime=self.period,
            out_min=0,
            out_max=self.period,
            noiseband=self.noiseband)

        self.running = True
        self.autotune_active = True
        self.timer_loop = time.time()

        self.logger.info(
            "PID Autotune started with options: "
            "Measurement Device: {}, Measurement: {}, Output: {}, Output_Channel: {}, Setpoint: {}, "
            "Period: {}, Noise Band: {}, Outstep: {}, DIrection: {}".format(
                self.measurement_device_id,
                self.measurement_measurement_id,
                self.output_device_id,
                self.output_channel,
                self.setpoint,
                self.period,
                self.noiseband,
                self.outstep,
                self.direction))

    def loop(self):
        if self.output_channel is None:
            self.logger.error("Cannot start PID Autotune: Could not find output channel.")
            self.deactivate_self()
            return

        if self.timer_loop > time.time() or not self.autotune_active:
            return

        while time.time() > self.timer_loop:
            self.timer_loop = self.timer_loop + self.period

        last_measurement = self.get_last_measurement(
            self.measurement_device_id,
            self.measurement_measurement_id)

        if not self.autotune.run(last_measurement[1]):
            self.control_variable = self.autotune.output

            self.logger.info('')
            self.logger.info("state: {}".format(self.autotune.state))
            self.logger.info("output: {}".format(self.autotune.output))
        else:
            # Autotune has finished
            timestamp = time.time() - self.timestamp
            self.autotune_active = False
            self.logger.info('Autotune has finished')
            self.logger.info('time:  {0} min'.format(round(timestamp / 60)))
            self.logger.info('state: {0}'.format(self.autotune.state))

            if self.autotune.state == PIDAutotune.STATE_SUCCEEDED:
                self.logger.info('Autotune was successful')
                for rule in self.autotune.tuning_rules:
                    params = self.autotune.get_pid_parameters(rule)
                    self.logger.info('')
                    self.logger.info('rule: {0}'.format(rule))
                    self.logger.info('Kp: {0}'.format(params.Kp))
                    self.logger.info('Ki: {0}'.format(params.Ki))
                    self.logger.info('Kd: {0}'.format(params.Kd))
            else:
                self.logger.info('Autotune was not successful')

            # Finally, deactivate controller
            self.deactivate_self()
            return

        self.control.output_on(
            self.output_device_id,
            output_type='sec',
            output_channel=self.output_channel,
            amount=self.control_variable)

    def deactivate_self(self):
        self.logger.info("Deactivating Autotune Function")
        with session_scope(MYCODO_DB_PATH) as new_session:
            mod_cont = new_session.query(CustomController).filter(
                CustomController.unique_id == self.unique_id).first()
            mod_cont.is_activated = False
            new_session.commit()

        deactivate_controller = threading.Thread(
            target=self.control.controller_deactivate,
            args=(self.unique_id,))
        deactivate_controller.start()
