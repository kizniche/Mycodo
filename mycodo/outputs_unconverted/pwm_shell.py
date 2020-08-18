# coding=utf-8
#
# command_pwm.py - Output for executing linux commands with PWM
#
import copy

from flask_babel import lazy_gettext
from sqlalchemy import and_

from mycodo.databases.models import DeviceMeasurements
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import add_measurements_influxdb
from mycodo.utils.influx import read_last_influxdb
from mycodo.utils.system_pi import cmd_output
from mycodo.utils.system_pi import return_measurement_info

# Measurements
measurements_dict = {
    0: {
        'measurement': 'duty_cycle',
        'unit': 'percent'
    }
}

channels_dict = {
    0: {
        'types': ['pwm'],
        'measurements': [0]
    }
}

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'command_pwm',
    'output_name': "{} Shell Script".format(lazy_gettext('PWM')),
    'output_library': 'subprocess.Popen',
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'output_types': ['pwm'],

    'message': 'Commands will be executed in the Linux shell by the specified user when the duty cycle '
               'is set for this output. The string "((duty_cycle))" in the command will be replaced with '
               'the duty cycle being set prior to execution.',

    'options_enabled': [
        'command_pwm',
        'command_execute_user',
        'pwm_state_startup',
        'pwm_state_shutdown',
        'button_send_duty_cycle'
    ],
    'options_disabled': ['interface'],

    'interfaces': ['SHELL']
}


class OutputModule(AbstractOutput):
    """
    An output support class that operates an output
    """
    def __init__(self, output, testing=False):
        super(OutputModule, self).__init__(output, testing=testing, name=__name__)

        self.state_startup = None
        self.startup_value = None
        self.state_shutdown = None
        self.shutdown_value = None
        self.pwm_state = None
        self.pwm_command = None
        self.linux_command_user = None
        self.pwm_invert_signal = None

    def setup_output(self):
        self.setup_on_off_output(OUTPUT_INFORMATION)
        self.state_startup = self.output.state_startup
        self.startup_value = self.output.startup_value
        self.state_shutdown = self.output.state_shutdown
        self.shutdown_value = self.output.shutdown_value
        self.pwm_command = self.output.pwm_command
        self.linux_command_user = self.output.linux_command_user
        self.pwm_invert_signal = self.output.pwm_invert_signal

        if self.pwm_command:
            self.output_setup = True

            if self.state_startup == '0':
                self.output_switch('off')
            elif self.state_startup == 'set_duty_cycle':
                self.output_switch('on', amount=self.startup_value)
            elif self.state_startup == 'last_duty_cycle':
                device_measurement = db_retrieve_table_daemon(DeviceMeasurements).filter(
                    and_(DeviceMeasurements.device_id == self.unique_id,
                         DeviceMeasurements.channel == 0)).first()

                last_measurement = None
                if device_measurement:
                    channel, unit, measurement = return_measurement_info(device_measurement, None)
                    last_measurement = read_last_influxdb(
                        self.unique_id,
                        unit,
                        channel,
                        measure=measurement,
                        duration_sec=None)

                if last_measurement:
                    self.logger.info(
                        "Setting startup duty cycle to last known value of {dc} %".format(
                            dc=last_measurement[1]))
                    self.output_switch('on', amount=last_measurement[1])
                else:
                    self.logger.error(
                        "Output instructed at startup to be set to "
                        "the last known duty cycle, but a last known "
                        "duty cycle could not be found in the measurement "
                        "database")
        else:
            self.logger.error("Output must have command set")

    def output_switch(self, state, output_type=None, amount=None, output_channel=None):
        measure_dict = copy.deepcopy(measurements_dict)

        if self.pwm_command:
            if state == 'on' and 0 <= amount <= 100:
                if self.pwm_invert_signal:
                    amount = 100.0 - abs(amount)
            elif state == 'off':
                if self.pwm_invert_signal:
                    amount = 100
                else:
                    amount = 0
            else:
                return

            self.pwm_state = amount

            cmd = self.pwm_command.replace('((duty_cycle))', str(amount))
            cmd_return, cmd_error, cmd_status = cmd_output(cmd, user=self.linux_command_user)

            measure_dict[0]['value'] = self.pwm_state
            add_measurements_influxdb(self.unique_id, measure_dict)

            self.logger.debug("Duty cycle set to {dc:.2f} %".format(dc=amount))
            self.logger.debug(
                "Output duty cycle {duty_cycle} command returned: "
                "Status: {stat}, "
                "Output: '{ret}', "
                "Error: '{err}'".format(
                    duty_cycle=amount,
                    stat=cmd_status,
                    ret=cmd_return,
                    err=cmd_error))

    def is_on(self, output_channel=None):
        if self.is_setup():
            if self.pwm_state:
                return self.pwm_state
            return False

    def is_setup(self):
        return self.output_setup

    def stop_output(self):
        """ Called when Output is stopped """
        if self.state_shutdown == '0':
            self.output_switch('off')
        elif self.state_shutdown == 'set_duty_cycle':
            self.output_switch('on', amount=self.shutdown_value)
        self.running = False
