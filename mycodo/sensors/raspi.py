# coding=utf-8
from __future__ import division

import subprocess
import time
from itertools import izip


class RaspberryPiCPUTemp(object):
    def __init__(self):
        self._temperature = 0
        self.running = True

    def read(self):
        temperature = []
        # create average of two readings
        for x in range(2):
            time.sleep(1)
            temperature.append(self.get_measurement())
        if (None in temperature or
                max(temperature)-min(temperature) > 10):
            self._temperature = None
            return 1
        else:
            self._temperature = sum(temperature, 0.0) / len(temperature)
            return 0

    def get_measurement(self):
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

    def stopSensor(self):
        self.running = False


class RaspberryPiGPUTemp(object):
    def __init__(self):
        self._temperature = 0
        self.running = True

    def read(self):
        gputempstr = subprocess.check_output(('/opt/vc/bin/vcgencmd', 'measure_temp'))
        gputempc = float(gputempstr.split('=')[1].split("'")[0])
        self._temperature = gputempc

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
        self.read()
        response = {
            'temperature': self.temperature
        }
        return response

    def stopSensor(self):
        self.running = False


if __name__ == "__main__":
    cpu_temp = RaspberryPiCPUTemp()
    gpu_temp = RaspberryPiGPUTemp()

    for cpu, gpu in izip(cpu_temp, gpu_temp):
        print("GPU: {}".format(gpu['temperature']))
        print("CPU: {}".format(cpu['temperature']))
        time.sleep(.5)
