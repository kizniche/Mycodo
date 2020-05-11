# coding=utf-8
#
# pwm.py - Output for GPIO PWM
#
from flask_babel import lazy_gettext

from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.system_pi import cmd_output

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
    'output_name': lazy_gettext('PWM (GPIO)'),
    'measurements_dict': measurements_dict,

    'output_types': ['pwm'],

    'message': 'Information about this output.',

    'dependencies_module': []
}


class OutputModule(AbstractOutput):
    """
    An output support class that operates an output
    """
    def __init__(self, output, testing=False):
        super(OutputModule, self).__init__(output, testing=testing, name=__name__)

        self.pwm_state = None
        self.pwm_output = None

        if not testing:
            import pigpio
            self.pigpio = pigpio

            self.pwm_library = output.pwm_library
            self.output_pin = output.pin
            self.pwm_hertz = output.pwm_hertz

    def output_switch(self, state, amount=None, duty_cycle=None):
        if state == 'on':
            if self.pwm_library == 'pigpio_hardware':
                self.pwm_output.hardware_PWM(
                    self.output_pin,
                    self.pwm_hertz,
                    int(abs(duty_cycle) * 10000))
            elif self.pwm_library == 'pigpio_any':
                self.pwm_output.set_PWM_frequency(
                    self.output_pin,
                    self.pwm_hertz)
                calc_duty_cycle = int((abs(duty_cycle) / 100.0) * 255)
                if calc_duty_cycle > 255:
                    calc_duty_cycle = 255
                if calc_duty_cycle < 0:
                    calc_duty_cycle = 0
                self.pwm_output.set_PWM_dutycycle(
                    self.output_pin,
                    calc_duty_cycle)
            self.pwm_state = abs(duty_cycle)
        elif state == 'off':
            if self.pwm_library == 'pigpio_hardware':
                self.pwm_output.hardware_PWM(
                    self.output_pin,
                    self.pwm_hertz, 0)
            elif self.pwm_library == 'pigpio_any':
                self.pwm_output.set_PWM_frequency(
                    self.output_pin,
                    self.pwm_hertz)
                self.pwm_output.set_PWM_dutycycle(
                    self.output_pin, 0)
            self.pwm_state = None

    def is_on(self):
        if self.pwm_output:
            self.pwm_output.get_PWM_dutycycle(self.output_pin)
        return False

    def is_setup(self):
        if self.pwm_output:
            return True
        return False

    def setup_output(self):
        if self.output_pin is None:
            self.logger.error("Invalid pin for output: {}.".format(
                self.output_pin))
            return

        if self.pwm_hertz <= 0:
            msg = "PWM Hertz must be a positive value"
            self.logger.error(msg)
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
            self.logger.info("Output setup on pin {}".format(self.output_pin))
        except Exception as except_msg:
            self.logger.exception(
                "Output was unable to be setup on pin {pin}: {err}".format(
                    pin=self.output_pin, err=except_msg))
