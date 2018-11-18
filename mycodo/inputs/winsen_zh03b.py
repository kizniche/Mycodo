# coding=utf-8
#
# From https://github.com/Theoi-Meteoroi/Winsen_ZH03B
#
import logging
import time

from flask_babel import lazy_gettext

from mycodo.databases.models import DeviceMeasurements
from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import is_device
from mycodo.utils.database import db_retrieve_table_daemon


def constraints_pass_fan_seconds(value):
    """
    Check if the user input is acceptable
    :param value: float
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure value is positive
    if value <= 0:
        all_passed = False
        errors.append("Must be a positive value")
    return all_passed, errors


# Measurements
measurements_dict = {
    0: {
        'measurement': 'particulate_matter_1_0',
        'unit': 'ug_m3'
    },
    1: {
        'measurement': 'particulate_matter_2_5',
        'unit': 'ug_m3'
    },
    2: {
        'measurement': 'particulate_matter_10_0',
        'unit': 'ug_m3'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'WINSEN_ZH03B',
    'input_manufacturer': 'Winsen',
    'input_name': 'ZH03B',
    'measurements_name': 'Particulates',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'measurements_select',
        'uart_location',
        'uart_baud_rate',
        'custom_options',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'binascii', 'binascii')
    ],

    'interfaces': ['UART'],
    'uart_location': '/dev/ttyAMA0',
    'uart_baud_rate': 9600,

    'custom_options': [
        {
            'id': 'fan_modulate',
            'type': 'bool',
            'default_value': False,
            'name': lazy_gettext('Fan Off After Measure'),
            'phrase': lazy_gettext('Turn the fan on only during the measurement')
        },
        {
            'id': 'fan_seconds',
            'type': 'float',
            'default_value': 50.0,
            'constraints_pass': constraints_pass_fan_seconds,
            'name': lazy_gettext('Fan On Duration'),
            'phrase': lazy_gettext('How long to turn the fan on (seconds) before acquiring measurements')
        }
    ]
}


class InputModule(AbstractInput):
    """ A sensor support class that monitors the WINSEN_ZH03B's particulate concentration """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.winsen_zh03b")
        self._measurements = None
        self.fan_is_on = False

        if not testing:
            import serial
            import binascii
            self.logger = logging.getLogger(
                "mycodo.winsen_zh03b_{id}".format(id=input_dev.unique_id.split('-')[0]))

            self.device_measurements = db_retrieve_table_daemon(
                DeviceMeasurements).filter(
                    DeviceMeasurements.device_id == input_dev.unique_id)

            self.binascii = binascii
            self.uart_location = input_dev.uart_location
            self.baud_rate = input_dev.baud_rate
            # Check if device is valid
            self.serial_device = is_device(self.uart_location)

            self.fan_modulate = True
            self.fan_seconds = 50.0

            if input_dev.custom_options:
                for each_option in input_dev.custom_options.split(';'):
                    option = each_option.split(',')[0]
                    value = each_option.split(',')[1]
                    if option == 'fan_modulate':
                        self.fan_modulate = bool(value)
                    elif option == 'fan_seconds':
                        self.fan_seconds = float(value)

            if self.serial_device:
                try:
                    self.ser = serial.Serial(
                        port=self.serial_device,
                        baudrate=self.baud_rate,
                        parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE,
                        bytesize=serial.EIGHTBITS,
                        timeout=10
                    )
                    self.ser.flushInput()

                    if not self.fan_modulate:
                        self.dormant_mode('run')

                    time.sleep(0.1)

                except serial.SerialException:
                    self.logger.exception('Opening serial')
            else:
                self.logger.error(
                    'Could not open "{dev}". '
                    'Check the device location is correct.'.format(
                        dev=self.uart_location))

    def get_measurement(self):
        """ Gets the WINSEN_ZH03B's Particulate concentration in μg/m^3 via UART """
        if not self.serial_device:  # Don't measure if device isn't validated
            return None

        return_dict = measurements_dict.copy()

        self.logger.debug("Reading sample")

        if self.fan_modulate and not self.fan_is_on:
            # Allow the fan to run before querying sensor
            self.dormant_mode('run')
            start_time = time.time()
            while (self.running and
                    time.time() - start_time < self.fan_seconds):
                time.sleep(0.01)

        # Acquire measurements
        pm_1_0, pm_2_5, pm_10_0 = self.qa_read_sample()

        if pm_1_0 > 1000:
            pm_1_0 = 1001
            self.logger.error("PM1 measurement out of range (over 1000 ug/m^3)")
        if pm_2_5 > 1000:
            pm_2_5 = 1001
            self.logger.error("PM2.5 measurement out of range (over 1000 ug/m^3)")
        if pm_10_0 > 1000:
            pm_10_0 = 1001
            self.logger.error("PM10 measurement out of range (over 1000 ug/m^3)")

        if self.is_enabled(0):
            return_dict[0]['value'] = pm_1_0

        if self.is_enabled(1):
            return_dict[1]['value'] = pm_2_5

        if self.is_enabled(2):
            return_dict[2]['value'] = pm_10_0

        # Turn the fan off
        if self.fan_modulate:
            self.dormant_mode('sleep')  

        return return_dict

    @staticmethod
    def hex_to_byte(hex_str):
        """
        Convert a string hex byte values into a byte string. The Hex Byte values may
        or may not be space separated.
        """
        # The list comprehension implementation is fractionally slower in this case
        #
        #    hex_str = ''.join( hex_str.split(" ") )
        #    return ''.join( ["%c" % chr( int ( hex_str[i:i+2],16 ) ) \
        #                                   for i in range(0, len( hex_str ), 2) ] )
        bytes_ = []

        hex_str = ''.join(hex_str.split(" "))

        for i in range(0, len(hex_str), 2):
            bytes_.append(chr(int(hex_str[i:i + 2], 16)))

        return ''.join(bytes_)

    def set_qa(self):
        """
        Set ZH03B Question and Answer mode
        Returns:  Nothing
        """
        self.ser.write(b"\xFF\x01\x78\x41\x00\x00\x00\x00\x46")
        return

    def set_stream(self):
        """
        Set to default streaming mode of readings
        Returns: Nothing
        """
        self.ser.write(b"\xFF\x01\x78\x40\x00\x00\x00\x00\x47")
        return

    def qa_read_sample(self):
        """
        Q&A mode requires a command to obtain a reading sample
        Returns: int PM1, int PM25, int PM10
        """
        self.ser.flushInput()  # flush input buffer
        self.ser.write(b"\xFF\x01\x86\x00\x00\x00\x00\x00\x79")
        reading = self.hex_to_byte(((self.binascii.hexlify(self.ser.read(2))).hex()))
        pm_25 = int(self.hex_to_byte(((self.binascii.hexlify(self.ser.read(2))).hex())), 16)
        pm_10 = int(self.hex_to_byte(((self.binascii.hexlify(self.ser.read(2))).hex())), 16)
        pm_1 = int(self.hex_to_byte(((self.binascii.hexlify(self.ser.read(2))).hex())), 16)
        return pm_1, pm_25, pm_10

    def dormant_mode(self, pwr_status):
        """
        Turn dormant mode on or off. Must be on to measure.
        """
        #  Turn fan off
        if pwr_status == "sleep":
            self.ser.write(b"\xFF\x01\xA7\x01\x00\x00\x00\x00\x57")
            response = self.hex_to_byte(((self.binascii.hexlify(self.ser.read(3))).hex()))
            self.ser.flushInput()
            if response == "ffa701":
                self.fan_is_on = False
                return "FanOFF"
            else:
                return "FanERROR"

        #  Turn fan on
        if pwr_status == "run":
            self.ser.write(b"\xFF\x01\xA7\x00\x00\x00\x00\x00\x58")
            response = self.hex_to_byte(((self.binascii.hexlify(self.ser.read(3))).hex()))
            self.ser.flushInput()
            if response == "ffa701":
                self.fan_is_on = True
                return "FanON"
            else:
                return "FanERROR"

    def read_sample(self):
        """
        Read exactly one sample from the default mode streaming samples
        """
        self.ser.flushInput()  # flush input buffer
        sampled = False
        while not sampled and self.running:
            reading = self.hex_to_byte(((self.binascii.hexlify(self.ser.read(2))).hex()))
            if reading == "424d":
                sampled = True
                status = self.ser.read(8)
                pm_1 = int(self.hex_to_byte(((self.binascii.hexlify(self.ser.read(2))).hex())), 16)
                pm_25 = int(self.hex_to_byte(((self.binascii.hexlify(self.ser.read(2))).hex())), 16)
                pm_10 = int(self.hex_to_byte(((self.binascii.hexlify(self.ser.read(2))).hex())), 16)
                return pm_1, pm_25, pm_10
            else:
                continue
