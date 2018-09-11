# coding=utf-8
import logging
import time

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import convert_units
from mycodo.inputs.sensorutils import is_device

# Input information
INPUT_INFORMATION = {
    'unique_name_input': 'MH_Z19',
    'input_manufacturer': 'Winsen',
    'common_name_input': 'MH-Z19',
    'common_name_measurements': 'CO2',
    'unique_name_measurements': ['co2'],  # List of strings
    'dependencies_pip': ['serial'],  # List of strings
    'interfaces': ['UART'],  # List of strings
    'uart_location': '/dev/ttyAMA0',  # String
    'uart_baud_rate': 9600,  # Integer
    'options_disabled': ['interface'],
    'options_enabled': ['uart_location', 'uart_baud_rate', 'period',  'convert_unit', 'pre_output'],
}


class InputModule(AbstractInput):
    """ A sensor support class that monitors the MH-Z19's CO2 concentration """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.mh_z19")
        self._co2 = None

        if not testing:
            import serial
            self.logger = logging.getLogger(
                "mycodo.inputs.mhz19_{id}".format(id=input_dev.id))
            self.uart_location = input_dev.uart_location
            self.baud_rate = input_dev.baud_rate
            self.convert_to_unit = input_dev.convert_to_unit
            # Check if device is valid
            self.serial_device = is_device(self.uart_location)
            if self.serial_device:
                try:
                    self.ser = serial.Serial(self.serial_device,
                                             baudrate=self.baud_rate,
                                             timeout=1)
                except serial.SerialException:
                    self.logger.exception('Opening serial')
            else:
                self.logger.error(
                    'Could not open "{dev}". '
                    'Check the device location is correct.'.format(
                        dev=self.uart_location))

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(co2={co2})>".format(
            cls=type(self).__name__,
            co2="{0:.2f}".format(self._co2))

    def __str__(self):
        """ Return CO2 information """
        return "CO2: {co2}".format(co2="{0:.2f}".format(self._co2))

    def __iter__(self):  # must return an iterator
        """ MH-Z19 iterates through live CO2 readings """
        return self

    def next(self):
        """ Get next CO2 reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(co2=float('{0:.2f}'.format(self._co2)))

    @property
    def co2(self):
        """ CO2 concentration in ppmv """
        if self._co2 is None:  # update if needed
            self.read()
        return self._co2

    def get_measurement(self):
        """ Gets the MH-Z19's CO2 concentration in ppmv via UART"""
        self._co2 = None
        co2 = None

        if not self.serial_device:  # Don't measure if device isn't validated
            return None

        self.ser.flushInput()
        time.sleep(1)
        self.ser.write(bytearray([0xff, 0x01, 0x86, 0x00, 0x00, 0x00, 0x00, 0x00, 0x79]))
        time.sleep(.01)
        resp = self.ser.read(9)
        if len(resp) != 0:
            high = resp[2]
            low = resp[3]
            co2 = (high * 256) + low

        co2 = convert_units(
            'co2', 'ppm', self.convert_to_unit, co2)

        return co2

    def read(self):
        """
        Takes a reading from the MH-Z19 and updates the self._co2 value

        :returns: None on success or 1 on error
        """
        if self.acquiring_measurement:
            self.logger.error("Attempting to acquire a measurement when a"
                              " measurement is already being acquired.")
            return 1
        try:
            self.acquiring_measurement = True
            self._co2 = self.get_measurement()
            if self._co2 is not None:
                return  # success - no errors
        except Exception as e:
            self.logger.error(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        finally:
            self.acquiring_measurement = False
        return 1
