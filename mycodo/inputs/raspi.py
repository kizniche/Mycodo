# coding=utf-8
import logging
import subprocess

from mycodo.databases.models import DeviceMeasurements
from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.database import db_retrieve_table_daemon

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
    'input_name': 'RPi CPU/GPU Temperature',
    'measurements_name': 'Temperature',
    'measurements_dict': measurements_dict,
    'measurements_use_same_timestamp': True,

    'options_enabled': [
        'measurements_select',
        'period',
        'log_level_debug'
    ],
    'options_disabled': ['interface'],

    'interfaces': ['RPi']
}


class InputModule(AbstractInput):
    """ A sensor support class that monitors the raspberry pi's CPU and GPU temperatures """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.raspi")

        if not testing:
            self.logger = logging.getLogger(
                "mycodo.raspi_{id}".format(id=input_dev.unique_id.split('-')[0]))

            self.device_measurements = db_retrieve_table_daemon(
                DeviceMeasurements).filter(
                    DeviceMeasurements.device_id == input_dev.unique_id)

        if input_dev.log_level_debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

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

        return_dict = measurements_dict.copy()

        self.logger.debug("Acquiring Measurements...")

        if self.is_enabled(0):
            # CPU temperature
            with open('/sys/class/thermal/thermal_zone0/temp') as cpu_temp_file:
                temp_cpu = float(cpu_temp_file.read()) / 1000
                self.set_value(return_dict, 0, temp_cpu)
                self.logger.debug("CPU Temperature: {}".format(temp_cpu))

        if self.is_enabled(1):
            # GPU temperature
            temperature_gpu = subprocess.check_output(
                ('/opt/vc/bin/vcgencmd', 'measure_temp'))
            temp_gpu = float(temperature_gpu.split(b'=')[1].split(b"'")[0])
            self.set_value(return_dict, 1, temp_gpu)
            self.logger.debug("GPU Temperature: {}".format(temp_gpu))

        return return_dict
