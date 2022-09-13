# coding=utf-8
#
# pump_grove_motor_driver_v1_3.py - Output for Grove I2C Motor Driver (v1.3)
#
import threading
import time

import copy
from flask_babel import lazy_gettext

from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import OutputChannel
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.constraints_pass import constraints_pass_percent
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
    'output_name_unique': 'grove_i2c_motor_driver_v1_3',
    'output_name': "{}: Grove I2C Motor Driver (Board v1.3)".format(lazy_gettext('Peristaltic Pump')),
    'output_manufacturer': 'Grove',
    'output_library': 'smbus2',
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'output_types': ['volume', 'on_off'],

    'url_manufacturer': 'https://wiki.seeedstudio.com/Grove-I2C_Motor_Driver_V1.3',

    'message': 'Controls the Grove I2C Motor Driver Board (v1.3). Both motors will turn at the same time. This output can also dispense volumes of fluid if the motors are attached to peristaltic pumps.',

    'options_enabled': [
        'i2c_location',
        'button_on',
        'button_send_volume',
        'button_send_duration'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'smbus2', 'smbus2==0.4.1')
    ],

    'interfaces': ['I2C'],
    'i2c_address_editable': True,
    'i2c_address_default': '0x0f',

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
            'default_value': 100,
            'constraints_pass': constraints_pass_percent,
            'name': 'Motor Speed (0 - 100)',
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
            'name': lazy_gettext('Flow Rate Method'),
            'phrase': lazy_gettext('The flow rate to use when pumping a volume')
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
            'id': 'fastest_dispense_rate_ml_min',
            'type': 'float',
            'default_value': 100.0,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Fastest Rate (ml/min)',
            'phrase': 'The fastest rate that the pump can dispense (ml/min)'
        }
    ],
}


class OutputModule(AbstractOutput):
    """An output support class that operates an output."""
    def __init__(self, output, testing=False):
        super().__init__(output, testing=testing, name=__name__)

        self.motor = None
        self.currently_dispensing = False

        output_channels = db_retrieve_table_daemon(
            OutputChannel).filter(OutputChannel.output_id == self.output.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            OUTPUT_INFORMATION['custom_channel_options'], output_channels)

    def initialize(self):
        import smbus2

        self.setup_on_off_output(OUTPUT_INFORMATION)
        self.motor = None
        try:
            self.logger.debug("I2C: Address: {}, Bus: {}".format(
                self.output.i2c_location, self.output.i2c_bus))
            if self.output.i2c_location:
                self.motor = MotorDriver(
                    smbus2,
                    self.output.i2c_bus,
                    self.output.i2c_location)
                self.output_setup = True
        except:
            self.logger.exception("Could not set up output")
            return

    def output_switch(self, state, output_type=None, amount=None, output_channel=None):
        if not self.is_setup():
            msg = "Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info."
            self.logger.error(msg)
            return msg

        direction = "CW"
        self.motor.motor_direction_set("cw")
        if amount and amount < 0:
            direction = "CCW"
            self.motor.motor_direction_set("ccw")

        self.logger.debug("state: {}, output_type: {}, amount: {} (direction: {})".format(
            state, output_type, amount, direction))

        if state == 'off':
            if self.currently_dispensing:
                self.currently_dispensing = False
            self.logger.debug("Output turned off")
            self.motor.motor_speed_set_a_b(0, 0)

        elif (state == 'on' and
              output_type in ['vol', None] and
              amount not in [0, None]):
            if self.currently_dispensing:
                self.logger.debug(
                    "Pump instructed to turn on for a duration while it's "
                    "already dispensing. Overriding current dispense with "
                    "new instruction.")

            if self.options_channels['flow_mode'][0] == 'fastest_flow_rate':
                total_dispense_seconds = abs(amount) / self.options_channels['fastest_dispense_rate_ml_min'][0] * 60

                msg = "Turning pump on for {sec:.1f} seconds {dir} to " \
                      "dispense {ml:.1f} ml (at {rate:.1f} ml/min, " \
                      "the fastest flow rate).".format(
                    sec=total_dispense_seconds,
                    dir=direction,
                    ml=abs(amount),
                    rate=self.options_channels['fastest_dispense_rate_ml_min'][0])
                self.logger.debug(msg)

                write_db = threading.Thread(
                    target=self.dispense_volume_fastest,
                    args=(amount, total_dispense_seconds,))
                write_db.start()
                return

            elif self.options_channels['flow_mode'][0] == 'specify_flow_rate':
                slowest_rate_ml_min = (self.options_channels['fastest_dispense_rate_ml_min'][0] /
                                       60 * self.options_channels['minimum_sec_on_per_min'][0])
                if self.options_channels['flow_rate'][0] < slowest_rate_ml_min:
                    self.logger.debug(
                        "Instructed to dispense {ir:.1f} ml/min, "
                        "however the slowest rate is set to {sr:.1f} ml/min.".format(
                            ir=self.options_channels['flow_rate'][0], sr=slowest_rate_ml_min))
                    dispense_rate = slowest_rate_ml_min
                elif self.options_channels['flow_rate'][0] > self.options_channels['fastest_dispense_rate_ml_min'][0]:
                    self.logger.debug(
                        "Instructed to dispense {ir:.1f} ml/min, "
                        "however the fastest rate is set to {fr:.1f} ml/min.".format(
                            ir=self.options_channels['flow_rate'][0],
                            fr=self.options_channels['fastest_dispense_rate_ml_min'][0]))
                    dispense_rate = self.options_channels['fastest_dispense_rate_ml_min'][0]
                else:
                    dispense_rate = self.options_channels['flow_rate'][0]

                self.logger.debug("Turning pump on to dispense {ml:.1f} ml {dir} at {rate:.1f} ml/min.".format(
                    ml=amount, dir=direction, rate=dispense_rate))

                write_db = threading.Thread(
                    target=self.dispense_volume_rate,
                    args=(amount, dispense_rate,))
                write_db.start()
                return

            else:
                self.logger.error("Invalid Output Mode: '{}'. Make sure it is properly set.".format(
                    self.options_channels['flow_mode'][0]))
                return

        elif state == 'on' and output_type == 'sec':
            if self.currently_dispensing:
                self.logger.debug(
                    "Pump instructed to turn on while it's already dispensing. "
                    "Overriding current dispense with new instruction.")
            self.logger.debug("Output turned on {}".format(direction))
            self.motor.motor_speed_set_a_b(
                self.options_channels['motor_speed'][0],
                self.options_channels['motor_speed'][1])

        else:
            self.logger.error(
                "Invalid parameters: State: {state}, Type: {ot}, "
                "Mode: {mod}, Amount: {amt}, Flow Rate: {fr}".format(
                    state=state,
                    ot=output_type,
                    mod=self.options_channels['flow_mode'][0],
                    amt=amount,
                    fr=self.options_channels['flow_rate'][0]))
            return

    def dispense_volume_fastest(self, amount, total_dispense_seconds):
        """Dispense at fastest flow rate, a 100 % duty cycle"""
        self.currently_dispensing = True
        self.logger.debug("Output turned on")

        self.motor.motor_speed_set_a_b(100, 100)
        if amount > 0:
            self.motor.motor_direction_set("cw")
        elif amount < 0:
            self.motor.motor_direction_set("ccw")
        timer_dispense = time.time() + total_dispense_seconds

        while time.time() < timer_dispense and self.currently_dispensing:
            time.sleep(0.01)

        self.motor.motor_speed_set_a_b(0, 0)
        self.currently_dispensing = False
        self.logger.debug("Output turned off")
        self.record_dispersal(amount, total_dispense_seconds, total_dispense_seconds)

    def dispense_volume_rate(self, amount, dispense_rate):
        """Dispense at a specific flow rate"""
        # Calculate total disperse time and durations to cycle on/off to reach total volume
        total_dispense_seconds = abs(amount) / dispense_rate * 60
        self.logger.debug("Total duration to run: {0:.1f} seconds".format(total_dispense_seconds))

        duty_cycle = dispense_rate / self.options_channels['fastest_dispense_rate_ml_min'][0]
        self.logger.debug("Duty Cycle: {0:.1f} %".format(duty_cycle * 100))

        total_seconds_on = total_dispense_seconds * duty_cycle
        self.logger.debug("Total seconds on: {0:.1f}".format(total_seconds_on))

        total_seconds_off = total_dispense_seconds - total_seconds_on
        self.logger.debug("Total seconds off: {0:.1f}".format(total_seconds_off))

        repeat_seconds_on = self.options_channels['minimum_sec_on_per_min'][0]
        repeat_seconds_off = self.options_channels['minimum_sec_on_per_min'][0] / duty_cycle
        self.logger.debug(
            "Repeat for {rep:.2f} seconds: on {on:.1f} seconds, off {off:.1f} seconds".format(
                rep=repeat_seconds_off, on=repeat_seconds_on, off=repeat_seconds_off))

        self.currently_dispensing = True
        timer_dispense = time.time() + total_dispense_seconds

        if amount > 0:
            self.motor.motor_direction_set("cw")
        elif amount < 0:
            self.motor.motor_direction_set("ccw")

        while time.time() < timer_dispense and self.currently_dispensing:
            # On for duration
            self.logger.debug("Output turned on")
            self.motor.motor_speed_set_a_b(
                self.options_channels['motor_speed'][0],
                self.options_channels['motor_speed'][1])
            timer_dispense_on = time.time() + repeat_seconds_on
            while time.time() < timer_dispense_on and self.currently_dispensing:
                time.sleep(0.01)

            # Off for duration
            self.logger.debug("Output turned off")
            self.motor.motor_speed_set_a_b(0, 0)
            timer_dispense_off = time.time() + repeat_seconds_off
            while time.time() < timer_dispense_off and self.currently_dispensing:
                time.sleep(0.01)

        self.currently_dispensing = False
        self.record_dispersal(amount, total_seconds_on, total_dispense_seconds)

    def record_dispersal(self, amount, total_on_seconds, total_dispense_seconds):
        measure_dict = copy.deepcopy(measurements_dict)
        measure_dict[0]['value'] = total_on_seconds
        measure_dict[1]['value'] = amount
        measure_dict[2]['value'] = total_dispense_seconds
        add_measurements_influxdb(self.unique_id, measure_dict)

    def is_on(self, output_channel=None):
        if self.is_setup():
            if self.currently_dispensing:
                return True

    def is_setup(self):
        return self.output_setup


class MotorDriver(object):
    MotorSpeedSet = 0x82
    PWMFrequenceSet = 0x84
    DirectionSet = 0xaa
    MotorSetA = 0xa1
    MotorSetB = 0xa5
    Nothing = 0x01
    EnableStepper = 0x1a
    UnenableStepper = 0x1b
    Stepernu = 0x1c
    I2CAddress = '0x0f'  # Set the address of the I2CMotorDriver

    def __init__(self, smbus, i2c_bus, i2c_address=I2CAddress):
        self.bus = smbus.SMBus(i2c_bus)
        self.i2c_bus = i2c_bus
        self.i2c_address = i2c_address

    def __repr__(self):
        return "MotorDriver(i2c_bus={}, i2c_address={})".format(self.i2c_bus, self.i2c_address)

    def map_vals(self, value, leftMin, leftMax, rightMin, rightMax):
        """Map speed from 0-100 to 0-255"""
        # http://stackoverflow.com/questions/1969240/mapping-a-range-of-values-to-another
        # Figure out how 'wide' each range is
        leftSpan = leftMax - leftMin
        rightSpan = rightMax - rightMin

        # Convert the left range into a 0-1 range (float)
        valueScaled = float(value - leftMin) / float(leftSpan)

        # Convert the 0-1 range into a value in the right range.
        return int(rightMin + (valueScaled * rightSpan))

    def motor_speed_set_a_b(self, speed_a, speed_b):
        """Set motor speed."""
        motor_speed_a = self.map_vals(speed_a, 0, 100, 0, 255)
        motor_speed_b = self.map_vals(speed_b, 0, 100, 0, 255)
        self.bus.write_i2c_block_data(
            int(str(self.i2c_address), 16),
            self.MotorSpeedSet,
            [motor_speed_a, motor_speed_b])
        time.sleep(0.02)

    def motor_direction_set(self, direction):
        """Set motor direction, either cw or ccw."""
        if direction == "cw":
            direction_address = 0b1010
        elif direction == "ccw":
            direction_address = 0b1001
        else:
            return
        self.bus.write_i2c_block_data(
            int(str(self.i2c_address), 16),
            self.DirectionSet,
            [direction_address, 0])
        time.sleep(0.02)
