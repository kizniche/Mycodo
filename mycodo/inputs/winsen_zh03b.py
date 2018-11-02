# coding=utf-8
#
# From https://github.com/Theoi-Meteoroi/Winsen_ZH03B
#
import logging
import time

from flask_babel import lazy_gettext

from mycodo.databases.models import InputMeasurements
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
measurements = {
    'particulate_matter_1_0': {
        'μg_m3': {0: {}}
    },
    'particulate_matter_2_5': {
        'μg_m3': {0: {}}
    },
    'particulate_matter_10_0': {
        'μg_m3': {0: {}}
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'WINSEN_ZH03B',
    'input_manufacturer': 'Winsen',
    'input_name': 'ZH03B',
    'measurements_name': 'Particulates',
    'measurements_dict': measurements,

    'options_enabled': [
        'measurements_select',
        'measurements_convert',
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
            'default_value': True,
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

        if not testing:
            import serial
            import binascii
            self.logger = logging.getLogger(
                "mycodo.winsen_zh03b_{id}".format(id=input_dev.unique_id.split('-')[0]))

            self.input_measurements = db_retrieve_table_daemon(
                InputMeasurements).filter(
                    InputMeasurements.input_id == input_dev.unique_id).all()

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
                        self.fan_state = self.DormantMode('run')

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

        return_dict = {
            'particulate_matter_1_0': {
                'μg_m3': {}
            },
            'particulate_matter_2_5': {
                'μg_m3': {}
            },
            'particulate_matter_10_0': {
                'μg_m3': {}
            }
        }

        pm_1_0 = None
        pm_2_5 = None
        pm_10_0 = None

        self.logger.debug("Reading sample")

        try:
            if self.fan_modulate:
                # Allow the fan to run before querying sensor
                self.DormantMode('run')
                start_time = time.time()
                while (self.running and
                        time.time() - start_time < self.fan_seconds):
                    time.sleep(0.01)

            # Acquire measurements
            pm_1_0, pm_2_5, pm_10_0 = self.QAReadSample()

            if pm_1_0 > 1000:
                pm_1_0 = 1001
                self.logger.error("PM1 measurement out of range (over 1000 ug/m^3)")
            if pm_2_5 > 1000:
                pm_2_5 = 1001
                self.logger.error("PM2.5 measurement out of range (over 1000 ug/m^3)")
            if pm_10_0 > 1000:
                pm_10_0 = 1001
                self.logger.error("PM10 measurement out of range (over 1000 ug/m^3)")

            if self.is_enabled('particulate_matter_1_0', 'μg_m3', 0):
                return_dict['particulate_matter_1_0']['μg_m3'][0] = pm_1_0

            if self.is_enabled('particulate_matter_2_5', 'μg_m3', 0):
                return_dict['particulate_matter_2_5']['μg_m3'][0] = pm_2_5

            if self.is_enabled('particulate_matter_10_0', 'μg_m3', 0):
                return_dict['particulate_matter_10_0']['μg_m3'][0] = pm_10_0

            # Turn the fan off
            if self.fan_modulate:
                self.DormantMode('sleep')
        except:
            self.logger.exception("Exception while reading")
            return None

        return return_dict

    @staticmethod
    def HexToByte(hexStr):
        """
        Convert a string hex byte values into a byte string. The Hex Byte values may
        or may not be space separated.
        """
        # The list comprehension implementation is fractionally slower in this case
        #
        #    hexStr = ''.join( hexStr.split(" ") )
        #    return ''.join( ["%c" % chr( int ( hexStr[i:i+2],16 ) ) \
        #                                   for i in range(0, len( hexStr ), 2) ] )
        bytes = []

        hexStr = ''.join(hexStr.split(" "))

        for i in range(0, len(hexStr), 2):
            bytes.append(chr(int(hexStr[i:i + 2], 16)))

        return ''.join(bytes)

    def SetQA(self):
        """
        Set ZH03B Question and Answer mode
        Returns:  Nothing
        """
        self.ser.write(b"\xFF\x01\x78\x41\x00\x00\x00\x00\x46")
        return

    def SetStream(self):
        """
        Set to default streaming mode of readings
        Returns: Nothing
        """
        self.ser.write(b"\xFF\x01\x78\x40\x00\x00\x00\x00\x47")
        return

    def QAReadSample(self):
        """
        Q&A mode requires a command to obtain a reading sample
        Returns: int PM1, int PM25, int PM10
        """
        self.ser.flushInput()  # flush input buffer
        self.ser.write(b"\xFF\x01\x86\x00\x00\x00\x00\x00\x79")
        reading = self.HexToByte(((self.binascii.hexlify(self.ser.read(2))).hex()))
        PM25 = int(self.HexToByte(((self.binascii.hexlify(self.ser.read(2))).hex())), 16)
        PM10 = int(self.HexToByte(((self.binascii.hexlify(self.ser.read(2))).hex())), 16)
        PM1 = int(self.HexToByte(((self.binascii.hexlify(self.ser.read(2))).hex())), 16)
        return PM1, PM25, PM10

    def DormantMode(self, pwr_status):
        """
        Turn dormant mode on or off. Must be on to measure.
        """
        #  Turn fan off
        #
        if pwr_status == "sleep":
            self.ser.write(b"\xFF\x01\xA7\x01\x00\x00\x00\x00\x57")
            response = self.HexToByte(((self.binascii.hexlify(self.ser.read(3))).hex()))
            self.ser.flushInput()
            if response == "ffa701":
                return "FanOFF"
            else:
                return "FanERROR"

        #  Turn fan on
        #
        if pwr_status == "run":
            self.ser.write(b"\xFF\x01\xA7\x00\x00\x00\x00\x00\x58")
            response = self.HexToByte(((self.binascii.hexlify(self.ser.read(3))).hex()))
            self.ser.flushInput()
            if response == "ffa701":
                return "FanON"
            else:
                return "FanERROR"

    def ReadSample(self):
        """
        Read exactly one sample from the default mode streaming samples
        """
        self.ser.flushInput()  # flush input buffer
        sampled = False
        while not sampled and self.running:
            reading = self.HexToByte(((self.binascii.hexlify(self.ser.read(2))).hex()))
            if reading == "424d":
                sampled = True
                status = self.ser.read(8)
                PM1 = int(self.HexToByte(((self.binascii.hexlify(self.ser.read(2))).hex())), 16)
                PM25 = int(self.HexToByte(((self.binascii.hexlify(self.ser.read(2))).hex())), 16)
                PM10 = int(self.HexToByte(((self.binascii.hexlify(self.ser.read(2))).hex())), 16)
                return PM1, PM25, PM10
            else:
                continue
