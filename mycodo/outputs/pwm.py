# coding=utf-8
#
# pwm.py - Output for GPIO PWM
#
from flask_babel import lazy_gettext

from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.influx import add_measurements_influxdb

# Measurements
measurements_dict = {
    0: {
        'measurement': 'duty_cycle',
        'unit': 'percent'
    }
}

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'pwm',
    'output_name': lazy_gettext('PWM'),
    'measurements_dict': measurements_dict,

    'on_state_internally_handled': False,
    'output_types': ['pwm'],

    'message': 'See the PWM section of the manual for PWM information and determining which '
               'pins may be used for each library option. ',

    'options_enabled': [
        'gpio_pin',
        'pwm_library',
        'pwm_frequency',
        'pwm_invert_signal',
        'pwm_state_startup',
        'pwm_state_shutdown',
        'trigger_functions_startup'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [],

    'interfaces': ['GPIO']
}


class OutputModule(AbstractOutput):
    """
    An output support class that operates an output
    """
    def __init__(self, output, testing=False):
        super(OutputModule, self).__init__(output, testing=testing, name=__name__)

        self.output_setup = None
        self.pwm_state = None
        self.pwm_output = None

        if not testing:
            import pigpio
            self.pigpio = pigpio

            self.output_unique_id = output.unique_id
            self.pwm_library = output.pwm_library
            self.output_pin = output.pin
            self.pwm_hertz = output.pwm_hertz
            self.pwm_invert_signal = output.pwm_invert_signal

    def output_switch(self, state, amount=None, duty_cycle=None):
        measure_dict = measurements_dict.copy()

        if state == 'on':
            if self.pwm_invert_signal:
                duty_cycle = 100.0 - abs(duty_cycle)
        elif state == 'off':
            if self.pwm_invert_signal:
                duty_cycle = 100
            else:
                duty_cycle = 0

        if self.pwm_library == 'pigpio_hardware':
            self.pwm_output.hardware_PWM(
                self.output_pin, self.pwm_hertz, int(duty_cycle * 10000))
        elif self.pwm_library == 'pigpio_any':
            self.pwm_output.set_PWM_frequency(self.output_pin, self.pwm_hertz)
            self.pwm_output.set_PWM_range(self.output_pin, 1000)
            self.pwm_output.set_PWM_dutycycle(
                self.output_pin, self.duty_cycle_to_pigpio_value(duty_cycle))

        self.pwm_state = duty_cycle

        measure_dict[0]['value'] = duty_cycle
        add_measurements_influxdb(self.output_unique_id, measure_dict)

        self.logger.debug("Duty cycle set to {dc:.2f} %".format(dc=duty_cycle))

    def is_on(self):
        if self.is_setup():
            response = self.pwm_output.get_PWM_dutycycle(self.output_pin)
            if self.pwm_library == 'pigpio_hardware':
                duty_cycle = response / 10000
            elif self.pwm_library == 'pigpio_any':
                duty_cycle = self.pigpio_value_to_duty_cycle(response)
            else:
                return None

            if duty_cycle > 0:
                return duty_cycle

            return False

    def is_setup(self):
        if self.output_setup:
            return True
        return False

    def setup_output(self):
        error = []
        if self.output_pin is None:
            error.append("Pin must be set")
        if self.pwm_hertz <= 0:
            error.append("PWM Hertz must be a positive value")
        if error:
            for each_error in error:
                self.logger.error(each_error)
            return

        try:
            self.pwm_output = self.pigpio.pi()
            if not self.pwm_output.connected:
                self.logger.error("Could not connect to pigpiod")
                self.pwm_output = None
                return
            if self.pwm_library == 'pigpio_hardware':
                self.pwm_output.hardware_PWM(
                    self.output_pin, self.pwm_hertz, 0)
            elif self.pwm_library == 'pigpio_any':
                self.pwm_output.set_PWM_frequency(
                    self.output_pin, self.pwm_hertz)
                self.pwm_output.set_PWM_dutycycle(
                    self.output_pin, 0)

            self.pwm_state = None
            self.output_setup = True
            self.logger.info("Output setup on pin {}".format(self.output_pin))
        except Exception as except_msg:
            self.logger.exception(
                "Output was unable to be setup on pin {pin}: {err}".format(
                    pin=self.output_pin, err=except_msg))

    @staticmethod
    def duty_cycle_to_pigpio_value(duty_cycle):
        pigpio_value = int((abs(duty_cycle) / 100.0) * 1000)
        if pigpio_value > 1000:
            pigpio_value = 1000
        elif pigpio_value < 0:
            pigpio_value = 0
        return pigpio_value

    @staticmethod
    def pigpio_value_to_duty_cycle(pigpio_value):
        duty_cycle = (abs(pigpio_value) / 1000.0) * 100
        if duty_cycle > 100:
            duty_cycle = 100
        elif duty_cycle < 0:
            duty_cycle = 0
        return duty_cycle
