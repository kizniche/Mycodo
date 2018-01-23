# coding=utf-8
from __future__ import division

import logging

from .base_input import AbstractInput

logger = logging.getLogger("mycodo.inputs.input_template")


class InputTemplate(AbstractInput):
    """ A sensor support class that returns a value from an Input """

    def __init__(self, i2c_address, i2c_bus, testing=False):
        super(InputTemplate, self).__init__()
        self._measurement = None
        self.i2c_address = i2c_address
        self.i2c_bus = i2c_bus

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(measurement={cond})>".format(
            cls=type(self).__name__,
            cond="{0:.2f}".format(self._measurement))

    def __str__(self):
        """ Return measurement """
        return "Measurement: {}".format("{0:.2f}".format(self._measurement))

    def __iter__(self):  # must return an iterator
        """ Iterates """
        return self

    def next(self):
        """ Get next measurement """
        if self.read():  # raised an error
            raise StopIteration  # required
        return {'measurement': float('{0:.2f}'.format(self._measurement))}

    @property
    def measurement(self):
        """ Describe the measurement """
        if self._measurement is None:  # update if needed
            self.read()
        return self._measurement

    def get_measurement(self):
        """ Describe what the new Input does to return a value """
        self._measurement = None

        ### Put code that conducts measurement here and return the measurement value
        measure = 10
        return measure

    def read(self):
        """
        Conducts the reading of the Input

        :returns: None on success or 1 on error
        """
        try:
            self._measurement = self.get_measurement()
            if self._measurement is not None:
                return  # success - no errors
        except Exception as e:
            logger.exception(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1
