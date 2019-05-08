# coding=utf-8
import logging
import time

from mycodo.inputs.base_input import AbstractInput
from mycodo.databases.models import DeviceMeasurements
from mycodo.utils.database import db_retrieve_table_daemon

list_sensitivity = []
for num in range(31, 255):
    list_sensitivity.append((num, str(num)))

# Measurements
measurements_dict = {
    0: {
        'measurement': 'light',
        'unit': 'lux'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'BH1750',
    'input_manufacturer': 'ROHM',
    'input_name': 'BH1750',
    'measurements_name': 'Light',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'i2c_location',
        'period',
        'resolution',
        'sensitivity',
        'pre_output',
        'log_level_debug'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'smbus2', 'smbus2')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x23', '0x5c'],
    'i2c_address_editable': False,
    'resolution': [
        (0, 'Low'),
        (1, 'High'),
        (2, 'High 2')
    ],
    'sensitivity': list_sensitivity
}

# Define some constants from the datasheet
POWER_DOWN = 0x00  # No active state
POWER_ON = 0x01  # Power on
RESET = 0x07  # Reset data register value
# Start measurement at 4lx resolution. Time typically 16ms.
CONTINUOUS_LOW_RES_MODE = 0x13
# Start measurement at 1lx resolution. Time typically 120ms
CONTINUOUS_HIGH_RES_MODE_1 = 0x10
# Start measurement at 0.5lx resolution. Time typically 120ms
CONTINUOUS_HIGH_RES_MODE_2 = 0x11
# Start measurement at 1lx resolution. Time typically 120ms
# Device is automatically set to Power Down after measurement.
ONE_TIME_HIGH_RES_MODE_1 = 0x20
# Start measurement at 0.5lx resolution. Time typically 120ms
# Device is automatically set to Power Down after measurement.
ONE_TIME_HIGH_RES_MODE_2 = 0x21
# Start measurement at 1lx resolution. Time typically 120ms
# Device is automatically set to Power Down after measurement.
ONE_TIME_LOW_RES_MODE = 0x23


class InputModule(AbstractInput):
    """ A sensor support class that monitors the DS18B20's lux """
    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.setup_logger()

        if not testing:
            from smbus2 import SMBus

            self.setup_logger(
                name=__name__, log_id=input_dev.unique_id.split('-')[0])

            self.device_measurements = db_retrieve_table_daemon(
                DeviceMeasurements).filter(
                    DeviceMeasurements.device_id == input_dev.unique_id)

            self.i2c_address = int(str(input_dev.i2c_location), 16)
            self.resolution = input_dev.resolution
            self.sensitivity = input_dev.sensitivity
            self.i2c_bus = SMBus(input_dev.i2c_bus)
            self.power_down()
            self.set_sensitivity(sensitivity=self.sensitivity)

            if input_dev.log_level_debug:
                self.logger.setLevel(logging.DEBUG)
            else:
                self.logger.setLevel(logging.INFO)

    @property
    def lux(self):
        """ BH1750 luminosity in lux """
        if self._measurements is None:  # update if needed
            self.read()
        return self._measurements

    def get_measurement(self):
        """ Gets the BH1750's lux """
        self.return_dict = measurements_dict.copy()

        if self.resolution == 0:
            lux = self.measure_low_res()
        elif self.resolution == 1:
            lux = self.measure_high_res()
        elif self.resolution == 2:
            lux = self.measure_high_res2()
        else:
            return None

        self.set_value(0, lux)

        return self.return_dict

    def _set_mode(self, mode):
        self.mode = mode
        self.i2c_bus.write_byte(self.i2c_address, self.mode)

    def power_down(self):
        self._set_mode(POWER_DOWN)

    def power_on(self):
        self._set_mode(POWER_ON)

    def reset(self):
        self.power_on()  # It has to be powered on before resetting
        self._set_mode(RESET)

    def cont_low_res(self):
        self._set_mode(CONTINUOUS_LOW_RES_MODE)

    def cont_high_res(self):
        self._set_mode(CONTINUOUS_HIGH_RES_MODE_1)

    def cont_high_res2(self):
        self._set_mode(CONTINUOUS_HIGH_RES_MODE_2)

    def oneshot_low_res(self):
        self._set_mode(ONE_TIME_LOW_RES_MODE)

    def oneshot_high_res(self):
        self._set_mode(ONE_TIME_HIGH_RES_MODE_1)

    def oneshot_high_res2(self):
        self._set_mode(ONE_TIME_HIGH_RES_MODE_2)

    def set_sensitivity(self, sensitivity=69):
        """
        Set the sensor sensitivity.
        Valid values are 31 (lowest) to 254 (highest), default is 69.
        """
        if sensitivity < 31:
            self.mtreg = 31
        elif sensitivity > 254:
            self.mtreg = 254
        else:
            self.mtreg = sensitivity
        self.power_on()
        self._set_mode(0x40 | (self.mtreg >> 5))
        self._set_mode(0x60 | (self.mtreg & 0x1f))
        self.power_down()

    def get_result(self):
        """ Return current measurement result in lx. """
        data = self.i2c_bus.read_word_data(self.i2c_address, self.mode)
        count = data >> 8 | (data & 0xff) << 8
        mode2coeff = 2 if (self.mode & 0x03) == 0x01 else 1
        ratio = 1 / (1.2 * (self.mtreg / 69.0) * mode2coeff)
        return ratio * count

    def wait_for_result(self, additional=0):
        basetime = 0.018 if (self.mode & 0x03) == 0x03 else 0.128
        time.sleep(basetime * (self.mtreg / 69.0) + additional)

    def do_measurement(self, mode, additional_delay=0):
        """
        Perform complete measurement using command specified by parameter
        mode with additional delay specified in parameter additional_delay.
        Return output value in Lx.
        """
        self.reset()
        self._set_mode(mode)
        self.wait_for_result(additional=additional_delay)
        return self.get_result()

    def measure_low_res(self, additional_delay=0):
        return self.do_measurement(ONE_TIME_LOW_RES_MODE, additional_delay)

    def measure_high_res(self, additional_delay=0):
        return self.do_measurement(ONE_TIME_HIGH_RES_MODE_1, additional_delay)

    def measure_high_res2(self, additional_delay=0):
        return self.do_measurement(ONE_TIME_HIGH_RES_MODE_2, additional_delay)
