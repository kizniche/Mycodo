# coding=utf-8
import logging

from mycodo.inputs.base_input import AbstractInput

# Input information
INPUT_INFORMATION = {
    'unique_name_input': 'GPIO_STATE',
    'input_manufacturer': 'RPi',
    'common_name_input': 'GPIO State',
    'common_name_measurements': 'GPIO State',
    'unique_name_measurements': ['gpio_state'],  # List of strings
    'dependencies_pypi': ['RPi.GPIO'],  # List of strings
    'interfaces': ['GPIO'],  # List of strings
    'options_disabled': ['interface'],
    'options_enabled': ['location', 'period', 'pre_output'],
}


class GPIOState(AbstractInput):
    """ A sensor support class that monitors the K30's CO2 concentration """

    def __init__(self, input_dev, testing=False):
        super(GPIOState, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.gpio_state")
        self._gpio_state = None

        if not testing:
            import RPi.GPIO as GPIO
            self.logger = logging.getLogger(
                "mycodo.inputs.gpio_state_{id}".format(id=input_dev.id))
            self.location = int(input_dev.location)
            self.gpio = GPIO
            self.gpio.setmode(self.gpio.BCM)
            self.gpio.setup(self.location, self.gpio.IN)

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(gpio_state={gpio_state})>".format(
            cls=type(self).__name__, gpio_state="{0}".format(self._gpio_state))

    def __str__(self):
        """ Return CO2 information """
        return "GPIO State: {gpio_state}".format(
            gpio_state="{0}".format(self._gpio_state))

    def __iter__(self):  # must return an iterator
        """ GPIOState iterates through GPIO state readings """
        return self

    def next(self):
        """ Get next GPIO State reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(gpio_state=float('{0}'.format(self._gpio_state)))

    @property
    def gpio_state(self):
        """ GPIO State as 0 (off) or 1 (on) """
        if self._gpio_state is None:  # update if needed
            self.read()
        return self._gpio_state

    def get_measurement(self):
        """ Gets the GPIO state via RPi.GPIO """
        self._gpio_state = None
        return self.gpio.input(self.location)

    def read(self):
        """
        Takes a reading from RPi.GPIO and updates the self._gpio_state value

        :returns: None on success or 1 on error
        """
        try:
            self._gpio_state = self.get_measurement()
            if self._gpio_state is not None:
                return  # success - no errors
        except Exception as e:
            self.logger.error(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1

    def stop_sensor(self):
        self.gpio.setmode(self.gpio.BCM)
        self.gpio.cleanup(self.location)