# coding=utf-8
import subprocess

from mycodo.inputs.base_input import AbstractInput

# Measurements
measurements_dict = {
    0: {
        'measurement': 'temperature',
        'unit': 'C',
        'name': 'CPU'
    },
    1: {
        'measurement': 'temperature',
        'unit': 'C',
        'name': 'GPU'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'RPi',
    'input_manufacturer': 'Raspberry Pi',
    'input_name': 'CPU/GPU Temperature',
    'measurements_name': 'Temperature',
    'measurements_dict': measurements_dict,
    'measurements_use_same_timestamp': True,

    'options_enabled': [
        'measurements_select',
        'period'
    ],
    'options_disabled': ['interface'],

    'interfaces': ['RPi']
}


class InputModule(AbstractInput):
    """ A sensor support class that monitors the raspberry pi's CPU and GPU temperatures """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

    def get_measurement(self):
        """ Gets the Raspberry pi's CPU and GPU temperatures in Celsius """
        # import psutil
        # import resource
        # open_files_count = 0
        # for proc in psutil.process_iter():
        #     if proc.open_files():
        #         open_files_count += 1
        # self.logger.info("Open files: {of}".format(of=open_files_count))
        # soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        # self.logger.info("LIMIT: Soft: {sft}, Hard: {hrd}".format(sft=soft, hrd=hard))

        self.return_dict = measurements_dict.copy()

        self.logger.debug("Acquiring Measurements...")

        if self.is_enabled(0):
            # CPU temperature
            with open('/sys/class/thermal/thermal_zone0/temp') as cpu_temp_file:
                temp_cpu = float(cpu_temp_file.read()) / 1000
                self.value_set(0, temp_cpu)
                self.logger.debug("CPU Temperature: {}".format(temp_cpu))

        if self.is_enabled(1):
            # GPU temperature
            temperature_gpu = subprocess.check_output(
                ('/opt/vc/bin/vcgencmd', 'measure_temp'))
            temp_gpu = float(temperature_gpu.split(b'=')[1].split(b"'")[0])
            self.value_set(1, temp_gpu)
            self.logger.debug("GPU Temperature: {}".format(temp_gpu))

        return self.return_dict
