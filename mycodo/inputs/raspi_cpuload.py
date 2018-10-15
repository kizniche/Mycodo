# coding=utf-8
import logging

import os

from mycodo.inputs.base_input import AbstractInput

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'RPiCPULoad',
    'input_manufacturer': 'Raspberry Pi',
    'input_name': 'RPi CPU Load',
    'measurements_name': 'CPULoad',
    'measurements_list': ['cpu_load_1m', 'cpu_load_5m', 'cpu_load_15m'],
    'options_enabled': ['location', 'period'],
    'options_disabled': ['interface'],

    'interfaces': ['RPi'],
    'location': {
        'title': 'Directory',
        'phrase': 'Directory to report the free space of',
        'options': [('/', '')]
    }
}


class InputModule(AbstractInput):
    """ A sensor support class that monitors the raspberry pi's cpu load """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.raspi_cpuload")
        self._cpu_load_1m = None
        self._cpu_load_5m = None
        self._cpu_load_15m = None

        if not testing:
            self.logger = logging.getLogger(
                "mycodo.raspi_cpuload_{id}".format(id=input_dev.unique_id.split('-')[0]))

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(cpu_load_1m={c1m})(cpu_load_5m={c5m})(cpu_load_15m={c15m})>".format(
            cls=type(self).__name__,
            c1m="{0:.2f}".format(self._cpu_load_1m),
            c5m="{0:.2f}".format(self._cpu_load_5m),
            c15m="{0:.2f}".format(self._cpu_load_15m))

    def __str__(self):
        """ Return CPU load information """
        return "CPU Load (1m): {c1m}, CPU Load (5m): {c5m}, CPU Load (15m): {c15m}".format(
            c1m="{:.2f}".format(self._cpu_load_1m),
            c5m="{:.2f}".format(self._cpu_load_5m),
            c15m="{:.2f}".format(self._cpu_load_15m))

    def __iter__(self):  # must return an iterator
        """ RaspberryPiCPULoad iterates through live temperature readings """
        return self

    def next(self):
        """ Get next load readings """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(cpu_load_1m=float('{0:.2f}'.format(self._cpu_load_1m)),
                    cpu_load_5m=float('{0:.2f}'.format(self._cpu_load_5m)),
                    cpu_load_15m=float('{0:.2f}'.format(self._cpu_load_15m)))

    @property
    def cpu_load_1m(self):
        """ CPU load for the past 1 minute """
        if self._cpu_load_1m is None:  # update if needed
            self.read()
        return self._cpu_load_1m

    @property
    def cpu_load_5m(self):
        """ CPU load for the past 5 minutes """
        if self._cpu_load_5m is None:  # update if needed
            self.read()
        return self._cpu_load_5m

    @property
    def cpu_load_15m(self):
        """ CPU load for the past 15 minutes """
        if self._cpu_load_15m is None:  # update if needed
            self.read()
        return self._cpu_load_15m

    @staticmethod
    def get_measurement():
        """ Gets the cpu load averages """
        return os.getloadavg()

    def read(self):
        """
        Takes a reading and updates the self._cpu_load_1m, self._cpu_load_5m,
        and self._cpu_load_15m values

        :returns: None on success or 1 on error
        """
        try:
            (self._cpu_load_1m,
             self._cpu_load_5m,
             self._cpu_load_15m) = self.get_measurement()
            if self._cpu_load_1m is not None:
                return  # success - no errors
        except Exception as e:
            self.logger.exception(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1
