# coding=utf-8
import logging
import time

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
    'measurements_name': 'CO2',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'uart_location',
        'uart_baud_rate',
        'period',
        'pre_output',
        'log_level_debug'
    ],
    'options_disabled': ['interface'],

    'interfaces': ['UART'],
    'uart_location': '/dev/ttyAMA0',
    'uart_baud_rate': 9600
}


class InputModule(AbstractInput):
    """ A sensor support class that monitors the K30's CO2 concentration """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.k30")

        if not testing:
            import serial
            self.logger = logging.getLogger(
                "mycodo.k30_{id}".format(
                    id=input_dev.unique_id.split('-')[0]))

            self.uart_location = input_dev.uart_location
            self.baud_rate = input_dev.baud_rate
            # Check if device is valid
            self.serial_device = is_device(self.uart_location)
            if self.serial_device:
                try:
                    self.ser = serial.Serial(
                        self.serial_device,
                        baudrate=self.baud_rate,
                        timeout=1)
                except serial.SerialException:
                    self.logger.exception('Opening serial')
            else:
                self.logger.error(
                    'Could not open "{dev}". '
                    'Check the device location is correct.'.format(
                        dev=self.uart_location))

            if input_dev.log_level_debug:
                self.logger.setLevel(logging.DEBUG)
            else:
                self.logger.setLevel(logging.INFO)

    def get_measurement(self):
        """ Gets the K30's CO2 concentration in ppmv via UART"""
        if not self.serial_device:  # Don't measure if device isn't validated
            return None

        return_dict = measurements_dict.copy()

        co2 = None

        self.ser.flushInput()
        time.sleep(1)
        self.ser.write(bytearray([0xfe, 0x44, 0x00, 0x08, 0x02, 0x9f, 0x25]))
        time.sleep(.01)
        resp = self.ser.read(7)
        if len(resp) != 0:
            high = resp[3]
            low = resp[4]
            co2 = (high * 256) + low

        return_dict[0]['value'] = co2

        return return_dict
