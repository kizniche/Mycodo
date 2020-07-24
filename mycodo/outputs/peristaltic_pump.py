# coding=utf-8
#
# atlas_ezo_pmp.py - Output for Atlas Scientific EZO Pump
#
import copy
import threading
import time

from flask_babel import lazy_gettext

from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.influx import add_measurements_influxdb


def constraints_pass_positive_value(mod_input, value):
    """
    Check if the user input is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: float or int
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure value is positive
    if value <= 0:
        all_passed = False
        errors.append("Must be a positive value")
    return all_passed, errors, mod_input

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
    }
}

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'peristaltic_pump',
    'output_name': "{} ({})".format(
        lazy_gettext('Peristaltic Pump'), lazy_gettext('Generic')),
    'output_library': 'RPi.GPIO',
    'measurements_dict': measurements_dict,

    'on_state_internally_handled': False,
    'output_types': ['volume', 'on_off'],

    'message': "This output turns a GPIO pin HIGH and LOW to control power to a generic peristaltic pump. "
               "The peristaltic pump can then be turned on for a duration or, after determining the pump's maximum "
               "flow rate, instructed to dispense a specific volume at the maximum rate or at a specified rate.",

    'options_enabled': [
        'gpio_pin',
        'on_off_state_on',
        'current_draw',
        'pump_output_mode',
        'pump_flow_rate',
        'button_on',
        'button_send_volume',
        'button_send_duration'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'RPi.GPIO', 'RPi.GPIO')
    ],

    'interfaces': ['GPIO'],
    
    'custom_options_message': "To accurately dispense specific volumes, the following options need to be correctly "
                              "set. To determine the flow rate of your pump, first purge the fluid line to remove "
                              "air. Next, turn the pump on for 60 seconds and collect the fluid that's dispensed. "
                              "Last, measure and enter the amount of fluid that was dispensed, in ml, into the "
                              "Fastest Rate (ml/min) field. Your pump should now be calibrated to dispense volumes "
                              "accurately. "
                              "Since Peristaltic Pump Output controllers are capable of accepting multiple different "
                              "dispersal value types, Default Dispersal Method must be set in order to specify whether "
                              "the peristaltic pump should output for a duration or a specific volume when other "
                              "controllers (such as PID controllers) send a value instructing it to dispense." ,
    'custom_options': [
        {
            'id': 'fastest_dispense_rate_ml_min',
            'type': 'float',
            'default_value': 150.0,
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
            'phrase': 'The minimum duration (seconds) the pump should be turned on for every 60 second period'
        }
    ]
}


class OutputModule(AbstractOutput):
    """
    An output support class that operates an output
    """
    def __init__(self, output, testing=False):
        super(OutputModule, self).__init__(output, testing=testing, name=__name__)

        self.output_setup = False
        self.GPIO = None
        self.pin = None
        self.on_state = None
        self.mode = None
        self.flow_rate = None

        self.currently_dispensing = False
        self.fastest_dispense_rate_ml_min = None
        self.minimum_sec_on_per_min = None
        self.setup_custom_options(
            OUTPUT_INFORMATION['custom_options'], output)

        if not testing:
            self.initialize_output()

    def initialize_output(self):
        import RPi.GPIO as GPIO

        self.GPIO = GPIO
        self.pin = self.output.pin
        self.on_state = self.output.on_state
        self.mode = self.output.output_mode
        self.flow_rate = self.output.flow_rate

    def dispense_volume_fastest(self, amount, total_dispense_seconds):
        """ Dispense at fastest flow rate, a 100 % duty cycle """
        self.currently_dispensing = True
        self.logger.debug("Output turned on")
        self.GPIO.output(self.pin, self.on_state)
        timer_dispense = time.time() + total_dispense_seconds

        while time.time() < timer_dispense and self.currently_dispensing:
            time.sleep(0.01)

        self.GPIO.output(self.pin, not self.on_state)
        self.currently_dispensing = False
        self.logger.debug("Output turned off")
        self.record_dispersal(amount, total_dispense_seconds, total_dispense_seconds)

    def dispense_volume_rate(self, amount, dispense_rate):
        """ Dispense at a specific flow rate """
        # Calculate total disperse time and durations to cycle on/off to reach total volume
        total_dispense_seconds = amount / dispense_rate * 60
        self.logger.debug("Total duration to run: {0:.1f} seconds".format(total_dispense_seconds))

        duty_cycle = dispense_rate / self.fastest_dispense_rate_ml_min
        self.logger.debug("Duty Cycle: {0:.1f} %".format(duty_cycle * 100))

        total_seconds_on = total_dispense_seconds * duty_cycle
        self.logger.debug("Total seconds on: {0:.1f}".format(total_seconds_on))

        total_seconds_off = total_dispense_seconds - total_seconds_on
        self.logger.debug("Total seconds off: {0:.1f}".format(total_seconds_off))

        repeat_seconds_on = self.minimum_sec_on_per_min
        repeat_seconds_off = self.minimum_sec_on_per_min / duty_cycle
        self.logger.debug("Repeat for {rep:.2f} seconds: on {on:.1f} seconds, off {off:.1f} seconds".format(
            rep=repeat_seconds_off, on=repeat_seconds_on, off=repeat_seconds_off))

        self.currently_dispensing = True
        timer_dispense = time.time() + total_dispense_seconds

        while time.time() < timer_dispense and self.currently_dispensing:
            # On for duration
            timer_dispense_on = time.time() + repeat_seconds_on
            self.logger.debug("Output turned on")
            self.GPIO.output(self.pin, self.on_state)
            while time.time() < timer_dispense_on and self.currently_dispensing:
                time.sleep(0.01)

            # Off for duration
            timer_dispense_off = time.time() + repeat_seconds_off
            self.logger.debug("Output turned off")
            self.GPIO.output(self.pin, not self.on_state)
            while time.time() < timer_dispense_off and self.currently_dispensing:
                time.sleep(0.01)

        self.GPIO.output(self.pin, not self.on_state)
        self.currently_dispensing = False
        self.logger.debug("Output turned off")
        self.record_dispersal(amount, total_seconds_on, total_dispense_seconds)

    def record_dispersal(self, amount, total_on_seconds, total_dispense_seconds):
        measure_dict = copy.deepcopy(measurements_dict)
        measure_dict[0]['value'] = total_on_seconds
        measure_dict[1]['value'] = amount
        measure_dict[2]['value'] = total_dispense_seconds
        add_measurements_influxdb(self.unique_id, measure_dict)

    def output_switch(self, state, output_type=None, amount=None, duty_cycle=None):
        self.logger.debug("state: {}, output_type: {}, amount: {}, duty_cycle: {}".format(
            state, output_type, amount, duty_cycle))

        if state == 'off':
            if self.currently_dispensing:
                self.currently_dispensing = False
            self.logger.debug("Output turned off")
            self.GPIO.output(self.pin, not self.on_state)

        elif state == 'on' and output_type == ['vol', None] and amount:
            if self.currently_dispensing:
                self.logger.debug("Pump instructed to turn on for a duration while it's already dispensing. "
                                  "Overriding current dispense with new instruction.")
            
            if self.mode == 'fastest_flow_rate':
                total_dispense_seconds = amount / self.fastest_dispense_rate_ml_min * 60
                msg = "Turning pump on for {sec:.1f} seconds to dispense {ml:.1f} ml (at {rate:.1f} ml/min, " \
                      "the fastest flow rate).".format(
                        sec=total_dispense_seconds, ml=amount, rate=self.fastest_dispense_rate_ml_min)
                self.logger.debug(msg)

                write_db = threading.Thread(
                    target=self.dispense_volume_fastest,
                    args=(amount, total_dispense_seconds,))
                write_db.start()
                return

            elif self.mode == 'specify_flow_rate':
                slowest_rate_ml_min = self.fastest_dispense_rate_ml_min / 60 * self.minimum_sec_on_per_min
                if self.flow_rate < slowest_rate_ml_min:
                    self.logger.debug(
                        "Instructed to dispense {ir:.1f} ml/min, "
                        "however the slowest rate is set to {sr:.1f} ml/min.".format(
                            ir=self.flow_rate, sr=slowest_rate_ml_min))
                    dispense_rate = slowest_rate_ml_min
                elif self.flow_rate > self.fastest_dispense_rate_ml_min:
                    self.logger.debug(
                        "Instructed to dispense {ir:.1f} ml/min, "
                        "however the fastest rate is set to {fr:.1f} ml/min.".format(
                            ir=self.flow_rate, fr=self.fastest_dispense_rate_ml_min))
                    dispense_rate = self.fastest_dispense_rate_ml_min
                else:
                    dispense_rate = self.flow_rate

                self.logger.debug(
                    "Turning pump on to dispense {ml:.1f} ml at {rate:.1f} ml/min.".format(
                        ml=amount, rate=dispense_rate))

                write_db = threading.Thread(
                    target=self.dispense_volume_rate,
                    args=(amount, dispense_rate,))
                write_db.start()
                return

            else:
                self.logger.error("Invalid Output Mode: '{}'. Make sure it is properly set.".format(self.mode))
                return

        elif state == 'on' and output_type == 'sec':
            if self.currently_dispensing:
                self.logger.debug("Pump instructed to turn on while it's already dispensing. "
                                  "Overriding current dispense with new instruction.")
            self.logger.debug("Output turned on")
            self.GPIO.output(self.pin, self.on_state)

        else:
            self.logger.error("Invalid parameters: State: {state}, Volume: {vol}, Flow Rate: {fr}".format(
                state=state, vol=amount, fr=self.flow_rate))
            return

    def is_on(self):
        if self.is_setup():
            try:
                if self.currently_dispensing:
                    return True
                return self.on_state == self.GPIO.input(self.pin)
            except Exception as e:
                self.logger.error("Status check error: {}".format(e))


    def is_setup(self):
        return self.output_setup

    def setup_output(self):
        if self.pin is None:
            self.logger.warning("Invalid pin for output: {}.".format(
                self.pin))
            return

        try:
            try:
                self.GPIO.setmode(self.GPIO.BCM)
                self.GPIO.setwarnings(True)
                self.GPIO.setup(self.pin, self.GPIO.OUT)
                self.GPIO.output(self.pin, not self.on_state)
                self.output_setup = True
            except Exception as e:
                self.logger.error("Setup error: {}".format(e))
            state = 'LOW' if self.on_state else 'HIGH'
            self.logger.info("Output setup on pin {pin} and turned OFF (OFF={state})".format(
                pin=self.pin, state=state))
        except Exception as except_msg:
            self.logger.exception("Output was unable to be setup on pin {pin} with trigger={trigger}: {err}".format(
                pin=self.pin,
                trigger=self.on_state,
                err=except_msg))
