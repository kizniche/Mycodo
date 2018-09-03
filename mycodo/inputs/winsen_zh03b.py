# coding=utf-8
#
# From https://github.com/Theoi-Meteoroi/Winsen_ZH03B
#
import logging

from .base_input import AbstractInput
from .sensorutils import is_device


class WINSEN_ZH03BSensor(AbstractInput):
    """ A sensor support class that monitors the WINSEN_ZH03B's particulate concentration """

    def __init__(self, input_dev, testing=False):
        super(WINSEN_ZH03BSensor, self).__init__()
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
            self.device_loc = input_dev.device_loc
            self.baud_rate = input_dev.baud_rate
            self.convert_to_unit = input_dev.convert_to_unit
            # Check if device is valid
            self.serial_device = is_device(self.device_loc)
            if self.serial_device:
                try:
                    self.ser = serial.Serial(
                        port=self.serial_device,
                        baudrate=self.baud_rate,
                        parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE,
                        bytesize=serial.EIGHTBITS,
                        timeout=1
                    )
                except serial.SerialException:
                    self.logger.exception('Opening serial')
            else:
                self.logger.error(
                    'Could not open "{dev}". '
                    'Check the device location is correct.'.format(
                        dev=self.device_loc))

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
        """ Gets the WINSEN_ZH03B's Particulate concentration in ppmv via UART"""
        if not self.serial_device:  # Don't measure if device isn't validated
            return None

        self._pm_1_0 = None
        self._pm_2_5 = None
        self._pm_10_0 = None
        pm_1_0 = None
        pm_2_5 = None
        pm_10_0 = None
        sampled = False

        self.ser.flushInput()  # flush input buffer

        while not sampled:
            sample = self.ser.read(2)

            # blank line check filter
            if sample != b'':
                reading = self.HexToByte(((self.binascii.hexlify(sample)).hex()))
                if reading == "424d":  # Start of data frame
                    sampled = True  # Sample will be captured
                    status = self.ser.read(8)  # Discard internal status bytes
                    pm_1_0 = int(self.HexToByte(((self.binascii.hexlify(self.ser.read(2))).hex())), 16)
                    pm_2_5 = int(self.HexToByte(((self.binascii.hexlify(self.ser.read(2))).hex())), 16)
                    pm_10_0 = int(self.HexToByte(((self.binascii.hexlify(self.ser.read(2))).hex())), 16)
            else:
                continue

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
            self.logger.error(
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