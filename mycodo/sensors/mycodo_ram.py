# coding=utf-8
import logging
import resource
from .base_sensor import AbstractSensor

from mycodo.mycodo_client import DaemonControl

logger = logging.getLogger("mycodo.sensors.mycodo_ram")


class MycodoRam(AbstractSensor):
    """
    A sensor support class that measures ram used by the Mycodo daemon

    """

    def __init__(self):
        super(MycodoRam, self).__init__()
        self.control = DaemonControl()
        self._ram = 0.0

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(ram={ram})>".format(
                cls=type(self).__name__,
                ram="{0:.2f}".format(self._ram))

    def __str__(self):
        """ Return measurement information """
        return "Ram: {ram}".format(
                ram="{0:.2f}".format(self._ram))

    def __iter__(self):  # must return an iterator
        """ SensorClass iterates through live measurement readings """
        return self

    def next(self):
        """ Get next measurement reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(ram_use=float('{0:.2f}'.format(self._ram)))

    def info(self):
        conditions_measured = [
            ("Ram", "ram", "float", "0.00",
             self._ram, self.ram)
        ]
        return conditions_measured

    @property
    def ram(self):
        """ Mycodo daemon ram in MegaBytes """
        if not self._ram:  # update if needed
            self.read()
        return self._ram

    def get_measurement(self):
        """ Gets the measurement in units by reading resource """
        ram = self.control.ram_use()
        return ram

    def read(self):
        """
        Takes a reading from resource and updates the self._ram

        :returns: None on success or 1 on error
        """
        try:
            self._ram = self.get_measurement()
            return  # success - no errors
        except Exception as e:
            logger.error("{cls} raised an exception when taking a reading: "
                         "{err}".format(cls=type(self).__name__, err=e))
        return 1
