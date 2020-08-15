# coding=utf-8
#
# pwm.py - Output for GPIO PWM
#
import copy

from flask_babel import lazy_gettext
from sqlalchemy import and_

from mycodo.databases.models import DeviceMeasurements
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import add_measurements_influxdb
from mycodo.utils.influx import read_last_influxdb
from mycodo.utils.system_pi import return_measurement_info

# Measurements
measurements_dict = {
    0: {
        'measurement': 'duty_cycle',
        'unit': 'percent'
    }
}

outputs_dict = {
    0: {
        'types': ['pwm'],
        'measurements': [0]
    }
}

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'pwm',
    'output_name': "{} GPIO".format(lazy_gettext('PWM')),
    'output_library': 'pigpio',
    'measurements_dict': measurements_dict,
    'outputs_dict': outputs_dict,
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
        'button_send_duty_cycle'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('internal', 'file-exists /opt/mycodo/pigpio_installed', 'pigpio')
    ],

    'interfaces': ['GPIO']
}


class OutputModule(AbstractOutput):
    """
    An output support class that operates an output
    """
    def __init__(self, output, testing=False):
        super(OutputModule, self).__init__(output, testing=testing, name=__name__)

        self.pigpio = None
        self.state_startup = None
        self.startup_value = None
        self.state_shutdown = None
        self.shutdown_value = None
        self.pwm_library = None
        self.pin = None
        self.pwm_hertz = None
        self.pwm_invert_signal = None
        self.pwm_output = None

    def setup_output(self):
        import pigpio

        self.pigpio = pigpio

        self.setup_on_off_output(OUTPUT_INFORMATION)
        self.state_startup = self.output.state_startup
        self.startup_value = self.output.startup_value
        self.state_shutdown = self.output.state_shutdown
        self.shutdown_value = self.output.shutdown_value
        self.pwm_library = self.output.pwm_library
        self.pin = self.output.pin
        self.pwm_hertz = self.output.pwm_hertz
        self.pwm_invert_signal = self.output.pwm_invert_signal

        error = []
        if self.pin is None:
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
                    self.pin, self.pwm_hertz, 0)
            elif self.pwm_library == 'pigpio_any':
                self.pwm_output.set_PWM_frequency(
                    self.pin, self.pwm_hertz)
                self.pwm_output.set_PWM_dutycycle(
                    self.pin, 0)

            self.output_setup = True
            self.logger.info("Output setup on pin {}".format(self.pin))

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
        except Exception as except_msg:
            self.logger.exception("Output was unable to be setup on pin {pin}: {err}".format(
                pin=self.pin, err=except_msg))

    def output_switch(self, state, output_type=None, amount=None, output_channel=None):
        measure_dict = copy.deepcopy(measurements_dict)

        if state == 'on':
            if self.pwm_invert_signal:
                amount = 100.0 - abs(amount)
        elif state == 'off':
            if self.pwm_invert_signal:
                amount = 100
            else:
                amount = 0

        if self.pwm_library == 'pigpio_hardware':
            self.pwm_output.hardware_PWM(self.pin, self.pwm_hertz, int(amount * 10000))
        elif self.pwm_library == 'pigpio_any':
            self.pwm_output.set_PWM_frequency(self.pin, self.pwm_hertz)
            self.pwm_output.set_PWM_range(self.pin, 1000)
            self.pwm_output.set_PWM_dutycycle(self.pin, self.duty_cycle_to_pigpio_value(amount))

        measure_dict[0]['value'] = amount
        add_measurements_influxdb(self.unique_id, measure_dict)

        self.logger.debug("Duty cycle set to {dc:.2f} %".format(dc=amount))

    def is_on(self, output_channel=None):
        if self.is_setup():
            response = self.pwm_output.get_PWM_dutycycle(self.pin)
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
        return self.output_setup

    def stop_output(self):
        """ Called when Output is stopped """
        if self.state_shutdown == '0':
            self.output_switch('off')
        elif self.state_shutdown == 'set_duty_cycle':
            self.output_switch('on', amount=self.shutdown_value)
        self.running = False

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
