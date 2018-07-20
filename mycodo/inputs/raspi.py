# coding=utf-8
import logging
import subprocess

from .base_input import AbstractInput
from .sensorutils import convert_units


class RaspberryPiCPUTemp(AbstractInput):
    """ A sensor support class that monitors the raspberry pi's cpu temperature """

    def __init__(self, input_dev, testing=False):
        super(RaspberryPiCPUTemp, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.raspi")
        self._temperature = None

        if not testing:
            self.logger = logging.getLogger(
                "mycodo.inputs.raspi_{id}".format(id=input_dev.id))
            self.convert_to_unit = input_dev.convert_to_unit

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(temperature={temp})>".format(
            cls=type(self).__name__,
            temp="{0:.2f}".format(self._temperature))

    def __str__(self):
        """ Return temperature information """
        return "Temperature: {0:.2f}".format(self._temperature)

    def __iter__(self):  # must return an iterator
        """ RaspberryPiCPUTemp iterates through live temperature readings """
        return self

    def next(self):
        """ Get next temperature reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(temperature=float('{0:.2f}'.format(self._temperature)))

    @property
    def temperature(self):
        """ CPU temperature in celsius """
        if self._temperature is None:  # update if needed
            self.read()
        return self._temperature

    def get_measurement(self):
        """ Gets the Raspberry pi's temperature in Celsius by reading the temp file and div by 1000 """
        # import psutil
        # import resource
        # open_files_count = 0
        # for proc in psutil.process_iter():
        #     if proc.open_files():
        #         open_files_count += 1
        # self.logger.info("Open files: {of}".format(of=open_files_count))
        # soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        # self.logger.info("LIMIT: Soft: {sft}, Hard: {hrd}".format(sft=soft, hrd=hard))
        with open('/sys/class/thermal/thermal_zone0/temp') as cpu_temp_file:
            temperature = convert_units(
                'temperature', 'C', self.convert_to_unit,
                float(cpu_temp_file.read()) / 1000)
            return temperature

    def read(self):
        """
        Takes a reading from the CPU and updates the self._temperature value

        :returns: None on success or 1 on error
        """
        try:
            self._temperature = self.get_measurement()
            if self._temperature is not None:
                return  # success - no errors
        except IOError as e:
            self.logger.error("{cls}.get_measurement() method raised IOError: "
                         "{err}".format(cls=type(self).__name__, err=e))
        except Exception as e:
            self.logger.exception("{cls} raised an exception when taking a reading: "
                             "{err}".format(cls=type(self).__name__, err=e))
        return 1


class RaspberryPiGPUTemp(AbstractInput):
    """ A sensor support class that monitors the raspberry pi's gpu temperature """

    def __init__(self, input_dev, testing=False):
        super(RaspberryPiGPUTemp, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.raspi")
        self._temperature = None

        if not testing:
            self.logger = logging.getLogger(
                "mycodo.inputs.raspi_{id}".format(id=input_dev.id))
            self.convert_to_unit = input_dev.convert_to_unit

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(temperature={temp})>".format(
            cls=type(self).__name__,
            temp="{0:.2f}".format(self._temperature))

    def __str__(self):
        """ Return temperature information """
        return "Temperature: {}".format("{0:.2f}".format(self._temperature))

    def __iter__(self):
        """ Support the iterator protocol """
        return self

    def next(self):
        """ Get next temperature reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(temperature=float('{0:.2f}'.format(self._temperature)))

    @property
    def temperature(self):
        """ returns the last temperature """
        if self._temperature is None:  # update if needed
            self.read()
        return self._temperature

    @staticmethod
    def get_measurement():
        """ Calls the vcgencmd in a subprocess and reads the GPU temperature """
        gputempstr = subprocess.check_output(('/opt/vc/bin/vcgencmd', 'measure_temp'))  # example output: temp=42.8'C
        return float(gputempstr.split('=')[1].split("'")[0])

    def read(self):
        """ updates the self._temperature """
        try:
            self._temperature = self.get_measurement()
            if self._temperature is not None:
                return  # success - no errors
        except subprocess.CalledProcessError as e:
            self.logger.exception(
                "{cls}.get_measurement() subprocess call raised: "
                "{err}".format(cls=type(self).__name__, err=e))
        except IOError as e:
            self.logger.exception(
                "{cls}.get_measurement() method raised IOError: "
                "{err}".format(cls=type(self).__name__, err=e))
        except Exception as e:
            self.logger.exception(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1
