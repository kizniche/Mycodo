# coding=utf-8
import time

import copy

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import is_device

# Measurements
measurements_dict = {
    0: {
        'measurement': 'co2',
        'unit': 'ppm'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'K30',
    'input_manufacturer': 'CO2Meter',
    'input_name': 'K30',
    'input_library': 'serial',
    'measurements_name': 'CO2',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.co2meter.com/products/k-30-co2-sensor-module',
    'url_datasheet': 'http://co2meters.com/Documentation/Datasheets/DS_SE_0118_CM_0024_Revised9%20(1).pdf',

    'options_enabled': [
        'uart_location',
        'uart_baud_rate',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'interfaces': ['UART'],
    'uart_location': '/dev/ttyAMA0',
    'uart_baud_rate': 9600
}


class InputModule(AbstractInput):
    """A sensor support class that monitors the K30's CO2 concentration."""
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.ser = None

        if not testing:
            self.try_initialize()

    def initialize(self):
        import serial

        # Check if device is valid
        if is_device(self.input_dev.uart_location):
            try:
                self.ser = serial.Serial(
                    port=self.input_dev.uart_location,
                    baudrate=self.input_dev.baud_rate,
                    timeout=1,
                    writeTimeout=5)
            except serial.SerialException:
                self.logger.exception('Opening serial')
        else:
            self.logger.error('Could not open "{dev}". Check the device location is correct.'.format(
                dev=self.input_dev.uart_location))

    def get_measurement(self):
        """Gets the K30's CO2 concentration in ppmv via UART."""
        if not self.ser:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        self.ser.flushInput()
        time.sleep(1)
        self.ser.write(bytearray([0xfe, 0x44, 0x00, 0x08, 0x02, 0x9f, 0x25]))
        time.sleep(.01)
        resp = self.ser.read(7)
        if len(resp) != 0:
            high = resp[3]
            low = resp[4]
            co2 = (high * 256) + low
            self.value_set(0, co2)

        return self.return_dict
