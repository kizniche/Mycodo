# coding=utf-8
#
# Example module for measuring with the K30 and sending
# the measurement to a serial device. For accompaniment with
# the The Things Network (TTN) Data Storage Input module
#
# Use this module to send measurements via serial to a
# LoRaWAN-enabled device, which transmits the data to TTN.
#
# Comment will be updated with other code to go along with this module
#
import time

import copy

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import is_device

airtime_seconds = 0.0515  # 51.5 ms
ttn_max_seconds_transmit_per_day = 30
max_transmissions_per_day = ttn_max_seconds_transmit_per_day / airtime_seconds
min_seconds_between_transmissions = 86400 / max_transmissions_per_day

# Measurements
measurements_dict = {
    0: {
        'measurement': 'co2',
        'unit': 'ppm'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'K30_TTN',
    'input_manufacturer': 'CO2Meter',
    'input_name': 'K30 (->Serial->TTN)',
    'input_library': 'serial',
    'measurements_name': 'CO2',
    'measurements_dict': measurements_dict,
    'measurements_use_same_timestamp': True,

    'message': "WARNING: This sensor doesn't have reverse-polarity protection, so if you accidentally reverse the voltage, you will damage the sensor.",

    'options_enabled': [
        'uart_location',
        'uart_baud_rate',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'serial', 'pyserial==3.5')
    ],

    'interfaces': ['UART'],
    'uart_location': '/dev/ttyAMA0',
    'uart_baud_rate': 9600,

    'custom_options': [
        {
            'id': 'serial_device',
            'type': 'text',
            'default_value': '/dev/ttyUSB0',
            'name': 'Serial Device',
            'phrase': 'The serial device to write to'
        }
    ]
}


class InputModule(AbstractInput):
    """ A sensor support class that monitors the K30's CO2 concentration """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.ser = None
        self.serial = None
        self.serial_send = None
        self.lock_file = "/var/lock/mycodo_ttn.lock"
        self.ttn_serial_error = False
        self.timer = 0

        # Initialize custom options
        self.serial_device = None

        if not testing:
            # Set custom options
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)

    def initialize_input(self):
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
            self.logger.error(
                'Could not open "{dev}". '
                'Check the device location is correct.'.format(
                    dev=self.input_dev.uart_location))

        self.serial = serial

        self.logger.debug(
            "Min time between transmissions: {} seconds".format(
                min_seconds_between_transmissions))

    def get_measurement(self):
        """ Gets the K30's CO2 concentration in ppmv via UART"""
        if not self.ser:  # Don't measure if device isn't validated
            return None

        self.return_dict = copy.deepcopy(measurements_dict)

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

        self.value_set(0, co2)

        try:
            now = time.time()
            if now > self.timer:
                self.timer = now + min_seconds_between_transmissions
                # "K" designates this data belonging to the K30
                string_send = 'K,{}'.format(self.value_get(0))

                if self.lock_acquire(self.lock_file, timeout=10):
                    try:
                        self.serial_send = self.serial.Serial(
                            port=self.serial_device,
                            baudrate=9600,
                            timeout=5,
                            writeTimeout=5)
                        self.serial_send.write(string_send.encode())
                        time.sleep(4)
                    finally:
                        self.lock_release(self.lock_file)
                self.ttn_serial_error = False
        except Exception as e:
            if not self.ttn_serial_error:
                # Only send this error once if it continually occurs
                self.logger.error("TTN: Could not send serial: {}".format(e))
                self.ttn_serial_error = True

        return self.return_dict
