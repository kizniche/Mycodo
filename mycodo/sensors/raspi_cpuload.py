# coding=utf-8

import os
import logging
from .base_sensor import AbstractSensor

logger = logging.getLogger("mycodo.sensors.raspi_cpuload")


class RaspberryPiCPULoad(AbstractSensor):
    """ A sensor support class that monitors the raspberry pi's cpu load """

    def __init__(self):
        super(RaspberryPiCPULoad, self).__init__()
        self._cpu_load_1m = 0.0
        self._cpu_load_5m = 0.0
        self._cpu_load_15m = 0.0

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

    def info(self):
        conditions_measured = [
            ("CPU Load (1m)", "cpu_load_1m", "float", "0.00",
             self._cpu_load_1m, self.cpu_load_1m),
            ("CPU Load (5m)", "cpu_load_5m", "float", "0.00",
             self._cpu_load_5m, self.cpu_load_5m),
            ("CPU Load (15m)", "cpu_load_15m", "float", "0.00",
             self._cpu_load_15m, self.cpu_load_15m)
        ]
        return conditions_measured

    @property
    def cpu_load_1m(self):
        """ CPU load for the past 1 minute """
        if not self._cpu_load_1m:  # update if needed
            self.read()
        return self._cpu_load_1m

    @property
    def cpu_load_5m(self):
        """ CPU load for the past 5 minutes """
        if not self._cpu_load_5m:  # update if needed
            self.read()
        return self._cpu_load_5m

    @property
    def cpu_load_15m(self):
        """ CPU load for the past 15 minutes """
        if not self._cpu_load_15m:  # update if needed
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
            return  # success - no errors
        except Exception as e:
            logger.error("{cls} raised an exception when taking a reading: "
                         "{err}".format(cls=type(self).__name__, err=e))
        return 1
