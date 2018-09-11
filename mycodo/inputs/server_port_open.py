# coding=utf-8
import logging
import os

from mycodo.inputs.base_input import AbstractInput

# Input information
INPUT_INFORMATION = {
    'unique_name_input': 'SERVER_PORT_OPEN',
    'input_manufacturer': 'Mycodo',
    'common_name_input': 'Server Port Open',
    'common_name_measurements': 'Boolean',
    'unique_name_measurements': ['boolean'],  # List of strings
    'dependencies_pip': [],  # List of strings
    'interfaces': ['Mycodo'],  # List of strings
    'location': {
        'title': 'Host Location',
        'phrase': 'Host name or IP address',
        'options': [('127.0.0.1', '')]
    },
    'port': 80,  # Integer
    'options_enabled': ['location', 'port', 'period', 'pre_output'],
    'options_disabled': ['interface']
}


class InputModule(AbstractInput):
    """
    A sensor support class that pings a server and returns 1 if it's up
    and 0 if it's down.
    """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.server_port_open")
        self._measurement = None

        if not testing:
            self.logger = logging.getLogger(
                "mycodo.inputs.server_port_open_{id}".format(id=input_dev.id))
            self.location = input_dev.location
            self.port = input_dev.port

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
            "nc -zv {host} {port} > /dev/null 2>&1".format(
                port=self.port,  host=self.location))
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
            self.logger.exception(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1
