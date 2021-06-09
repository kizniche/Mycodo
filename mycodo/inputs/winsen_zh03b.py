# coding=utf-8
#
# From https://github.com/Theoi-Meteoroi/Winsen_ZH03B
#
import time

import copy

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import is_device
from mycodo.utils.constraints_pass import constraints_pass_positive_value

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
    'input_library': 'serial',
    'measurements_name': 'Particulates',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.winsen-sensor.com/sensors/dust-sensor/zh3b.html',
    'url_datasheet': 'https://www.winsen-sensor.com/d/files/ZH03B.pdf',
    'url_product_purchase': '',

    'options_enabled': [
        'measurements_select',
        'uart_location',
        'uart_baud_rate',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'interfaces': ['UART'],
    'uart_location': '/dev/ttyAMA0',
    'uart_baud_rate': 9600,

    'custom_options': [
        {
            'id': 'fan_modulate',
            'type': 'bool',
            'default_value': False,
            'name': 'Fan Off After Measure',
            'phrase': 'Turn the fan on only during the measurement'
        },
        {
            'id': 'fan_seconds',
            'type': 'float',
            'default_value': 50.0,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Fan On Duration',
            'phrase': 'How long to turn the fan on (seconds) before acquiring measurements'
        },
        {
            'id': 'number_measurements',
            'type': 'integer',
            'default_value': 3,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Number of Measurements',
            'phrase': 'How many measurements to acquire. If more than 1 are acquired that are less than 1001, the average of the measurements will be stored.'
        }
    ]
}


class InputModule(AbstractInput):
    """ A sensor support class that monitors the WINSEN_ZH03B's particulate concentration """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.ser = None
        self.fan_is_on = False

        self.fan_modulate = None
        self.fan_seconds = None
        self.number_measurements = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.initialize_input()

    def initialize_input(self):
        import serial
        import binascii

        if is_device(self.input_dev.uart_location):
            try:
                self.binascii = binascii
                self.ser = serial.Serial(
                    port=self.input_dev.uart_location,
                    baudrate=self.input_dev.baud_rate,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS,
                    timeout=10,
                    writeTimeout=10
                )
                self.ser.flushInput()
                self.set_qa()

                if not self.fan_modulate:
                    self.dormant_mode('run')

                time.sleep(0.1)

            except serial.SerialException:
                self.logger.exception('Opening serial')
        else:
            self.logger.error('Could not open "{dev}". Check the device location is correct.'.format(
                dev=self.input_dev.uart_location))

    def get_measurement(self):
        """ Gets the WINSEN_ZH03B's Particulate concentration in μg/m^3 """
        if not self.ser:
            self.logger.error("Input not set up")
            return

        pm_1_0 = []
        pm_2_5 = []
        pm_10_0 = []

        self.return_dict = copy.deepcopy(measurements_dict)

        if self.fan_modulate and not self.fan_is_on:
            # Allow the fan to run for a duration before querying sensor
            self.dormant_mode('run')
            start_time = time.time()
            while self.running and time.time() - start_time < self.fan_seconds:
                time.sleep(0.01)

        # Acquire measurements
        for i in range(self.number_measurements):
            self.logger.debug("Acquiring measurement {}".format(i + 1))
            pm_1_0_tmp, pm_2_5_tmp, pm_10_0_tmp = self.qa_read_sample()
            self.logger.debug("Measurements: PM1 {}, PM2.5 {}, PM10 {}".format(pm_1_0_tmp, pm_2_5_tmp, pm_10_0_tmp))

            if pm_1_0_tmp > 1000:
                self.logger.debug("PM1 out of range (over 1000 ug/m^3): {}. Discarding.".format(pm_1_0_tmp))
            else:
                pm_1_0.append(pm_1_0_tmp)

            if pm_2_5_tmp > 1000:
                self.logger.debug("PM2.5 out of range (over 1000 ug/m^3): {}. Discarding.".format(pm_2_5_tmp))
            else:
                pm_2_5.append(pm_2_5_tmp)

            if pm_10_0_tmp > 1000:
                self.logger.debug("PM10 out of range (over 1000 ug/m^3): {}. Discarding.".format(pm_10_0_tmp))
            else:
                pm_10_0.append(pm_10_0_tmp)

            time.sleep(0.1)

        # Store measurements
        if len(pm_1_0) < 1 or len(pm_2_5) < 1 or len(pm_10_0) < 1:
            self.logger.debug("Error: Each particle size must have at least 1 valid measurement to store.")
        else:
            self.value_set(0, sum(pm_1_0) / len(pm_1_0))
            self.value_set(1, sum(pm_2_5) / len(pm_2_5))
            self.value_set(2, sum(pm_10_0) / len(pm_10_0))

        # Turn the fan off
        if self.fan_modulate:
            self.dormant_mode('sleep')

        return self.return_dict

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
