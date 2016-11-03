# coding=utf-8
from __future__ import division

import subprocess
import time
from itertools import izip


class RaspberryPiCPUTemp(object):
    def __init__(self):
        self._temperature = None

    def read(self):
        try:
            self._temperature = self.get_measurement()
        except IOError:
            return 1

    @staticmethod
    def get_measurement():
        with open('/sys/class/thermal/thermal_zone0/temp') as cpu_temp_file:
            raw_t = cpu_temp_file.read()
        return float(raw_t) / 1000

    @property
    def temperature(self):
        return self._temperature

    def __iter__(self):
        """
        Support the iterator protocol.
        """
        return self

    def next(self):
        """
        Call the read method and return temperature information.
        """
        if self.read():
            return None
        response = {
            'temperature': float("{0:.2f}".format(self.temperature))
        }
        return response


class RaspberryPiGPUTemp(object):
    def __init__(self):
        self._temperature = None

    def read(self):
        try:
            self._temperature = self.get_measurement()
        except IOError:
            return 1

    @staticmethod
    def get_measurement():
        gputempstr = subprocess.check_output(('/opt/vc/bin/vcgencmd', 'measure_temp'))
        return float(gputempstr.split('=')[1].split("'")[0])

    @property
    def temperature(self):
        return self._temperature

    def __iter__(self):
        """
        Support the iterator protocol.
        """
        return self

    def next(self):
        """
        Call the read method and return temperature information.
        """
        if self.read():
            return None
        response = {
            'temperature': float("{0:.1f}".format(self.temperature))
        }
        return response


if __name__ == "__main__":
    cpu_temp = RaspberryPiCPUTemp()
    gpu_temp = RaspberryPiGPUTemp()

    for cpu, gpu in izip(cpu_temp, gpu_temp):
        print("GPU: {}".format(gpu['temperature']))
        print("CPU: {}".format(cpu['temperature']))
        time.sleep(1)
