# coding=utf-8
from __future__ import division

import logging
import os

from .base_input import AbstractInput

logger = logging.getLogger("mycodo.inputs.server_ping")


class ServerPing(AbstractInput):
    """
    A sensor support class that pings a server and returns 1 if it's up
    and 0 if it's down.
    """

    def __init__(self, host, times, deadline, testing=False):
        super(ServerPing, self).__init__()
        self._measurement = None
        self.host = host
        self.times = times
        self.deadline = deadline

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(measurement={cond})>".format(
            cls=type(self).__name__,
            cond="{0:.2f}".format(self._measurement))

    def __str__(self):
        """ Return command output """
        return "Boolean: {}".format("{0}".format(self._measurement))

    def __iter__(self):  # must return an iterator
        """ ServerPing iterates through pinging a server """
        return self

    def next(self):
        """ Get next measurement """
        if self.read():  # raised an error
            raise StopIteration  # required
        return {'boolean': float('{0}'.format(self._measurement))}

    @property
    def measurement(self):
        """ Command returns a measurement """
        if self._measurement is None:  # update if needed
            self.read()
        return self._measurement

    def get_measurement(self):
        """ Determine if the return value of the command is a number """
        self._measurement = None

        response = os.system(
            "ping -c {times} -w {deadline} {host} > /dev/null 2>&1".format(
                times=self.times, deadline=self.deadline, host=self.host))
        if response == 0:
            return 1  # Server is up
        else:
            return 0  # Server is down

    def read(self):
        """
        Executes a command and updates the self._measurement value

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
