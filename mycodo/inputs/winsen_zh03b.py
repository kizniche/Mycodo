# coding=utf-8
#
# From https://github.com/Theoi-Meteoroi/Winsen_ZH03B
#
import logging
import time

from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import is_device


def constraints_pass_fan_seconds(value):
    """
    Check if the user input is acceptable
    :param value: value
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure value is positive
    if value <= 0:
        all_passed = False
        errors.append("Must be a positive value")
    return all_passed, errors


# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'WINSEN_ZH03B',
    'input_manufacturer': 'Winsen',
    'input_name': 'ZH03B',
    'measurements_name': 'Particulates',
    'measurements_list': ['particulate_matter_1_0', 'particulate_matter_2_5', 'particulate_matter_10_0'],
    'options_enabled': ['uart_location', 'uart_baud_rate', 'custom_options', 'period', 'convert_unit', 'pre_output'],
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
            'default_value': 5.0,
            'constraints_pass': constraints_pass_fan_seconds,
            'name': lazy_gettext('Fan On Duration'),
            'phrase': lazy_gettext('How long to turn the fan on (seconds) before acquiring measurements')
        },
    ]
}


class InputModule(AbstractInput):
    """ A sensor support class that monitors the WINSEN_ZH03B's particulate concentration """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.winsen_zh03b")
        self._pm_1_0 = None
        self._pm_2_5 = None
        self._pm_10_0 = None

        if not testing:
            import serial
            import binascii
            self.logger = logging.getLogger(
                "mycodo.inputs.winsen_zh03b_{id}".format(id=input_dev.id))
            self.binascii = binascii
            self.uart_location = input_dev.uart_location
            self.baud_rate = input_dev.baud_rate
            self.convert_to_unit = input_dev.convert_to_unit
            # Check if device is valid
            self.serial_device = is_device(self.uart_location)

            self.fan_state = None
            self.fan_modulate = True
            self.fan_seconds = 5.0

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
                except serial.SerialException:
                    self.logger.exception('Opening serial')
            else:
                self.logger.error(
                    'Could not open "{dev}". '
                    'Check the device location is correct.'.format(
                        dev=self.uart_location))

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(particulate_matter_1_0={pm_1_0})(particulate_matter_2_5={pm_2_5})(particulate_matter_10_0={pm_10_0})>".format(
            cls=type(self).__name__,
            pm_1_0="{0:.2f}".format(self._pm_1_0),
            pm_2_5="{0:.2f}".format(self._pm_2_5),
            pm_10_0="{0:.2f}".format(self._pm_10_0))

    def __str__(self):
        """ Return Particulate information """
        return "PM1: {pm_1_0}, PM2.5: {pm_2_5}, PM10: {pm_10_0}".format(
            pm_1_0="{0:.2f}".format(self._pm_1_0),
            pm_2_5="{0:.2f}".format(self._pm_2_5),
            pm_10_0="{0:.2f}".format(self._pm_10_0))

    def __iter__(self):  # must return an iterator
        """ WINSEN_ZH03B iterates through live Particulate readings """
        return self

    def next(self):
        """ Get next Particulate reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(particulate_matter_1_0=float('{0:.2f}'.format(self._pm_1_0)),
                    particulate_matter_2_5=float('{0:.2f}'.format(self._pm_2_5)),
                    particulate_matter_10_0=float('{0:.2f}'.format(self._pm_10_0)))

    @property
    def pm_1_0(self):
        """ PM1 concentration in μg/m^3 """
        if self._pm_1_0 is None:  # update if needed
            self.read()
        return self._pm_1_0

    @property
    def pm_2_5(self):
        """ PM2.5 concentration in μg/m^3 """
        if self._pm_2_5 is None:  # update if needed
            self.read()
        return self._pm_2_5

    @property
    def pm_10_0(self):
        """ PM10 concentration in μg/m^3 """
        if self._pm_10_0 is None:  # update if needed
            self.read()
        return self._pm_10_0

    def get_measurement(self):
        """ Gets the WINSEN_ZH03B's Particulate concentration in μg/m^3 via UART """
        if not self.serial_device:  # Don't measure if device isn't validated
            return None, None, None

        self._pm_1_0 = None
        self._pm_2_5 = None
        self._pm_10_0 = None
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

            # Turn the fan off
            if self.fan_modulate:
                self.DormantMode('sleep')
        except:
            self.logger.exception("Exception while reading")
            return None, None, None

        return pm_1_0, pm_2_5, pm_10_0

    def read(self):
        """
        Takes a reading from the WINSEN_ZH03B and updates the self._pm_1_0,
        self._pm_2_5, self._pm_10_0 values

        :returns: None on success or 1 on error
        """
        if self.acquiring_measurement:
            self.logger.error("Attempting to acquire a measurement when a"
                              " measurement is already being acquired.")
            return 1
        try:
            self.acquiring_measurement = True
            self._pm_1_0, self._pm_2_5, self._pm_10_0 = self.get_measurement()
            if self._pm_1_0 is not None:
                return  # success - no errors
        except Exception as e:
            self.logger.exception(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        finally:
            self.acquiring_measurement = False
        return 1

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
