# coding=utf-8
#
# grove_i2c_motor_driver_v1_0.py - Output for Grove I2C Motor Driver (TB6612FNG, Board v1.0)
#
import threading
import time

import copy
from flask_babel import lazy_gettext

from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import OutputChannel
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.constraints_pass import constraints_pass_positive_value
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import add_measurements_influxdb

# Measurements
measurements_dict = {
    0: {
        'measurement': 'duration_time',
        'unit': 's',
        'name': 'Pump On',
    },
    1: {
        'measurement': 'volume',
        'unit': 'ml',
        'name': 'Dispense Volume',
    },
    2: {
        'measurement': 'duration_time',
        'unit': 's',
        'name': 'Dispense Duration',
    },
    3: {
        'measurement': 'duration_time',
        'unit': 's',
        'name': 'Pump On',
    },
    4: {
        'measurement': 'volume',
        'unit': 'ml',
        'name': 'Dispense Volume',
    },
    5: {
        'measurement': 'duration_time',
        'unit': 's',
        'name': 'Dispense Duration',
    }
}

channels_dict = {
    0: {
        'name': 'Channel A',
        'types': ['volume', 'on_off'],
        'measurements': [0, 1, 2]
    },
    1: {
        'name': 'Channel B',
        'types': ['volume', 'on_off'],
        'measurements': [3, 4, 5]
    }
}

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'grove_i2c_motor_driver_v1_0',
    'output_name': "Grove I2C Motor Driver (TB6612FNG, Board v1.0)",
    'output_manufacturer': 'Grove',
    'output_library': 'smbus2',
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'output_types': ['volume', 'on_off'],

    'url_manufacturer': 'https://wiki.seeedstudio.com/Grove-I2C_Motor_Driver-TB6612FNG',

    'message': 'Controls the Grove I2C Motor Driver Board (v1.3). Both motors will turn at the same time. This output can also dispense volumes of fluid if the motors are attached to peristaltic pumps.',

    'options_enabled': [
        'i2c_location',
        'button_on',
        'button_send_volume',
        'button_send_duration'
    ],
    'options_disabled': [
        'interface'
    ],

    'dependencies_module': [
        ('pip-pypi', 'smbus2', 'smbus2')
    ],

    'interfaces': ['I2C'],

    'i2c_address_editable': True,
    'i2c_address_default': '0x14',

    'custom_options_message': "To accurately dispense specific volumes, the following options need to be correctly "
                              "set. To determine the flow rate of your pump, first purge the fluid line to remove "
                              "air. Next, turn the pump on for 60 seconds and collect the fluid that's dispensed. "
                              "Last, measure and enter the amount of fluid that was dispensed, in ml, into the "
                              "Fastest Rate (ml/min) field. Your pump should now be calibrated to dispense volumes "
                              "accurately. "
                              "Since Peristaltic Pump Output controllers are capable of accepting multiple different "
                              "dispersal value types, Default Dispersal Method must be set in order to specify whether "
                              "the peristaltic pump should output for a duration or a specific volume when other "
                              "controllers (such as PID controllers) send a value instructing it to dispense.",

    'custom_channel_options': [
        {
            'id': 'name',
            'type': 'text',
            'default_value': '',
            'required': False,
            'name': TRANSLATIONS['name']['title'],
            'phrase': TRANSLATIONS['name']['phrase']
        },
        {
            'id': 'motor_speed',
            'type': 'integer',
            'default_value': 255,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Motor Speed (0 - 255)',
            'phrase': 'The motor output that determines the speed'
        },
        {
            'id': 'flow_mode',
            'type': 'select',
            'default_value': 'fastest_flow_rate',
            'options_select': [
                ('fastest_flow_rate', 'Fastest Flow Rate'),
                ('specify_flow_rate', 'Specify Flow Rate')
            ],
            'name': 'Flow Rate Method',
            'phrase': 'The flow rate to use when pumping a volume'
        },
        {
            'id': 'flow_rate',
            'type': 'float',
            'default_value': 10.0,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Desired Flow Rate (ml/min)',
            'phrase': 'Desired flow rate in ml/minute when Specify Flow Rate set'
        },
        {
            'id': 'dispense_rate_ml_min',
            'type': 'float',
            'default_value': 100.0,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Fastest Rate (ml/min)',
            'phrase': 'The fastest rate that the pump can dispense (ml/min)'
        },
        {
            'id': 'minimum_sec_on_per_min',
            'type': 'float',
            'default_value': 1.0,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Minimum On (sec/min)',
            'phrase': 'The minimum duration (seconds) the pump turns on for every 60 second period (only used for Specify Flow Rate mode).'
        }
    ],

    'custom_actions_message':
        'The I2C address of the board can be changed. Enter a new address in the 0xYY format '
        '(e.g. 0x22, 0x50), then press Set I2C Address. Remember to deactivate the Output and '
        'change the I2C address option after setting the new address.',

    'custom_actions': [
        {
            'id': 'new_i2c_address',
            'type': 'text',
            'default_value': '0x14',
            'name': lazy_gettext('New I2C Address'),
            'phrase': 'The new I2C to set the sensor to'
        },
        {
            'id': 'set_i2c_address',
            'type': 'button',
            'name': lazy_gettext('Set I2C Address')
        }
    ]
}


class OutputModule(AbstractOutput):
    """An output support class that operates an output"""
    reg_write_run_cw = 0x02
    reg_write_run_ccw = 0x03
    reg_write_off = 0x00
    reg_change_i2c = 0x11

    def __init__(self, output, testing=False):
        super(OutputModule, self).__init__(output, testing=testing, name=__name__)

        self.i2c_address = None
        self.bus = None
        self.currently_dispensing = {0: False, 1: False}
        self.setting_i2c = False

        output_channels = db_retrieve_table_daemon(
            OutputChannel).filter(OutputChannel.output_id == self.output.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            OUTPUT_INFORMATION['custom_channel_options'], output_channels)

    def setup_output(self):
        import smbus2

        self.setup_on_off_output(OUTPUT_INFORMATION)
        try:
            self.logger.debug("I2C: Address: {}, Bus: {}".format(
                self.output.i2c_location, self.output.i2c_bus))
            if self.output.i2c_location:
                self.i2c_address = int(str(self.output.i2c_location), 16)
                self.bus = smbus2.SMBus(self.output.i2c_bus)
                self.output_setup = True
        except:
            self.logger.exception("Could not set up output")
            return

    def dispense_volume_fastest(self, channel, amount, total_dispense_seconds):
        """ Dispense at fastest flow rate, a 100 % duty cycle """
        if amount < 0:
            direction_reg = self.reg_write_run_ccw
        else:
            direction_reg = self.reg_write_run_cw

        self.currently_dispensing[channel] = True
        self.bus.write_i2c_block_data(
            self.i2c_address, direction_reg,
            [channel, self.options_channels['motor_speed'][channel]])
        self.logger.debug("Output turned on")

        timer_dispense = time.time() + total_dispense_seconds
        while time.time() < timer_dispense and self.currently_dispensing[channel]:
            time.sleep(0.01)

        self.bus.write_word_data(self.i2c_address, self.reg_write_off, channel)
        self.currently_dispensing[channel] = False
        self.logger.debug("Output turned off")

        self.record_dispersal(channel, amount, total_dispense_seconds, total_dispense_seconds)

    def dispense_volume_rate(self, channel, amount, dispense_rate):
        """ Dispense at a specific flow rate """
        if amount < 0:
            direction_reg = self.reg_write_run_ccw
        else:
            direction_reg = self.reg_write_run_cw

        # Calculate total disperse time and durations to cycle on/off to reach total volume
        total_dispense_seconds = abs(amount) / dispense_rate * 60
        self.logger.debug("Total duration to run: {0:.1f} seconds".format(total_dispense_seconds))

        duty_cycle = dispense_rate / self.options_channels['dispense_rate_ml_min'][channel]
        self.logger.debug("Duty Cycle: {0:.1f} %".format(duty_cycle * 100))

        total_seconds_on = total_dispense_seconds * duty_cycle
        self.logger.debug("Total seconds on: {0:.1f}".format(total_seconds_on))

        total_seconds_off = total_dispense_seconds - total_seconds_on
        self.logger.debug("Total seconds off: {0:.1f}".format(total_seconds_off))

        repeat_seconds_on = self.options_channels['minimum_sec_on_per_min'][channel]
        repeat_seconds_off = self.options_channels['minimum_sec_on_per_min'][channel] / duty_cycle
        self.logger.debug("Repeat for {rep:.2f} seconds: on {on:.1f} seconds, off {off:.1f} seconds".format(
            rep=repeat_seconds_off, on=repeat_seconds_on, off=repeat_seconds_off))

        self.currently_dispensing[channel] = True
        timer_dispense = time.time() + total_dispense_seconds

        while time.time() < timer_dispense and self.currently_dispensing[channel]:
            # On for duration
            self.logger.debug("Output turned on")
            self.bus.write_i2c_block_data(
                self.i2c_address, direction_reg,
                [channel, self.options_channels['motor_speed'][channel]])
            timer_dispense_on = time.time() + repeat_seconds_on
            while time.time() < timer_dispense_on and self.currently_dispensing[channel]:
                time.sleep(0.01)

            # Off for duration
            self.logger.debug("Output turned off")
            self.bus.write_word_data(self.i2c_address, self.reg_write_off, channel)
            timer_dispense_off = time.time() + repeat_seconds_off
            while time.time() < timer_dispense_off and self.currently_dispensing[channel]:
                time.sleep(0.01)

        self.currently_dispensing[channel] = False
        self.record_dispersal(channel, amount, total_seconds_on, total_dispense_seconds)

    def record_dispersal(self, channel, amount, total_on_seconds, total_dispense_seconds):
        measure_dict = copy.deepcopy(measurements_dict)
        if channel == 0:
            measure_dict[0]['value'] = total_on_seconds
            measure_dict[1]['value'] = amount
            measure_dict[2]['value'] = total_dispense_seconds
        elif channel == 1:
            measure_dict[3]['value'] = total_on_seconds
            measure_dict[4]['value'] = amount
            measure_dict[5]['value'] = total_dispense_seconds
        add_measurements_influxdb(self.unique_id, measure_dict)

    def output_switch(self, state, output_type=None, amount=None, output_channel=None):
        if self.setting_i2c:
            self.logger.error("Cannot operate output while I2C address is changing")
            return

        direction = "CW"
        direction_reg = self.reg_write_run_cw
        if amount and amount < 0:
            direction = "CCW"
            direction_reg = self.reg_write_run_ccw

        self.logger.debug(
            "state: {st}, channel: {ch}, output_type: {ot}, "
            "amount: {amt} (direction: {dir}), mode: {fm}, rate: {fr}".format(
                st=state,
                ch=output_channel,
                ot=output_type,
                amt=amount,
                dir=direction,
                fm=self.options_channels['flow_mode'][output_channel],
                fr=self.options_channels['flow_rate'][output_channel]))

        if state == 'off':
            if self.currently_dispensing[output_channel]:
                self.currently_dispensing[output_channel] = False
            self.logger.debug("Output turned off")
            self.bus.write_word_data(self.i2c_address, self.reg_write_off, output_channel)

        elif (amount and state == 'on' and
                output_type in ['vol', None]):

            if self.currently_dispensing[output_channel]:
                self.logger.debug(
                    "Pump instructed to turn on for a duration while it's "
                    "already dispensing. Overriding current dispense with "
                    "new instruction.")

            if self.options_channels['flow_mode'][output_channel] == 'fastest_flow_rate':
                total_dispense_seconds = (abs(amount) /
                                          self.options_channels['dispense_rate_ml_min'][output_channel] *
                                          60)

                msg = "Turning pump on for {sec:.1f} seconds {dir} to " \
                      "dispense {ml:.1f} ml (at {rate:.1f} ml/min, " \
                      "the fastest flow rate).".format(
                        sec=total_dispense_seconds,
                        dir=direction,
                        ml=abs(amount),
                        rate=self.options_channels['dispense_rate_ml_min'][output_channel])
                self.logger.debug(msg)

                write_db = threading.Thread(
                    target=self.dispense_volume_fastest,
                    args=(output_channel, amount, total_dispense_seconds,))
                write_db.start()
                return

            elif self.options_channels['flow_mode'][output_channel] == 'specify_flow_rate':
                slowest_rate_ml_min = (self.options_channels['dispense_rate_ml_min'][output_channel] /
                                       60 * self.options_channels['minimum_sec_on_per_min'][output_channel])
                if self.options_channels['flow_rate'][output_channel] < slowest_rate_ml_min:
                    self.logger.debug(
                        "Instructed to dispense {ir:.1f} ml/min, "
                        "however the slowest rate is set to {sr:.1f} ml/min.".format(
                            ir=self.options_channels['flow_rate'][output_channel], sr=slowest_rate_ml_min))
                    dispense_rate = slowest_rate_ml_min
                elif (self.options_channels['flow_rate'][output_channel] >
                        self.options_channels['dispense_rate_ml_min'][output_channel]):
                    self.logger.debug(
                        "Instructed to dispense {ir:.1f} ml/min, "
                        "however the fastest rate is set to {fr:.1f} ml/min.".format(
                            ir=self.options_channels['flow_rate'][output_channel],
                            fr=self.options_channels['dispense_rate_ml_min'][output_channel]))
                    dispense_rate = self.options_channels['dispense_rate_ml_min'][output_channel]
                else:
                    dispense_rate = self.options_channels['flow_rate'][output_channel]

                self.logger.debug(
                    "Turning pump on to dispense {ml:.1f} ml {dir} at {rate:.1f} ml/min.".format(
                        ml=amount, dir=direction, rate=dispense_rate))

                write_db = threading.Thread(
                    target=self.dispense_volume_rate,
                    args=(output_channel, amount, dispense_rate,))
                write_db.start()
                return

            else:
                self.logger.error(
                    "Invalid Output Mode: '{}'. Make sure it is properly set.".format(
                        self.options_channels['flow_mode'][output_channel]))
                return

        elif state == 'on' and output_type == 'sec':
            if self.currently_dispensing[output_channel]:
                self.logger.debug(
                    "Pump instructed to turn on while it's already dispensing. "
                    "Overriding current dispense with new instruction.")
            self.logger.debug("Speed: {0:.1f}".format(
                self.options_channels['motor_speed'][output_channel]))
            self.logger.debug("Output turned on {}".format(direction))
            self.bus.write_i2c_block_data(
                self.i2c_address, direction_reg,
                [output_channel, self.options_channels['motor_speed'][output_channel]])

        else:
            self.logger.error("Invalid parameters")
            return

    def is_on(self, output_channel=None):
        if self.is_setup():
            if self.currently_dispensing[output_channel]:
                return True

    def is_setup(self):
        return self.output_setup

    def set_i2c_address(self, args_dict):
        while self.currently_dispensing[0] or self.currently_dispensing[1]:
            time.sleep(0.1)

        try:
            self.setting_i2c = True

            if 'new_i2c_address' not in args_dict:
                self.logger.error(
                    "Cannot set new I2C address without an I2C address")
                return

            new_i2c_address = int(str(args_dict['new_i2c_address']), 16)
            self.bus.write_word_data(
                self.i2c_address, self.reg_change_i2c, new_i2c_address)
        except:
            self.logger.exception(
                "Could not parse I2C address {} or send it to the board. "
                "Ensure it's entered in the correct format and the board is accessible.".format(
                    args_dict['new_i2c_address']))
        finally:
            self.setting_i2c = False
