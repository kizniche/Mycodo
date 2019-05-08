# coding=utf-8
import logging
import time
from collections import OrderedDict
from datetime import datetime

import os

from mycodo.config import PATH_CAMERAS
from mycodo.databases.models import DeviceMeasurements
from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.image import generate_thermal_image_from_pixels
from mycodo.utils.system_pi import assure_path_exists

# Measurements
measurements_dict = OrderedDict()
for each_channel in range(64):
    measurements_dict[each_channel] = {
        'measurement': 'temperature',
        'unit': 'C'
    }

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'AMG8833',
    'input_manufacturer': 'Panasonic',
    'input_name': 'AMG8833',
    'measurements_name': '8x8 Temperature Grid',
    'measurements_dict': measurements_dict,
    'measurements_rescale': True,
    'scale_from_min': 0.0,
    'scale_from_max': 5.0,

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'period',
        'pre_output',
        'log_level_debug'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('apt', 'libjpeg-dev', 'libjpeg-dev'),
        ('apt', 'zlib1g-dev', 'zlib1g-dev'),
        ('pip-pypi', 'colour', 'colour'),
        ('pip-pypi', 'PIL', 'Pillow'),
        ('pip-git', 'Adafruit_AMG88xx', 'git://github.com/adafruit/Adafruit_AMG88xx_python.git#egg=adafruit-amg88xx')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x69', '0x68'],
    'i2c_address_editable': False,
}


class InputModule(AbstractInput):
    """ A sensor support class that monitors the AMG8833's temperature """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.setup_logger()
        self.save_image = False
        self.temp_max = None
        self.temp_min = None
        self.report = False
        self.scale = 2
        self.nx = 8
        self.ny = 8

        if not testing:
            from Adafruit_AMG88xx import Adafruit_AMG88xx

            self.setup_logger(
                name=__name__, log_id=input_dev.unique_id.split('-')[0])

            self.device_measurements = db_retrieve_table_daemon(
                DeviceMeasurements).filter(
                    DeviceMeasurements.device_id == input_dev.unique_id)

            self.Adafruit_AMG88xx = Adafruit_AMG88xx
            self.i2c_address = int(str(input_dev.i2c_location), 16)
            self.i2c_bus = input_dev.i2c_bus
            self.input_dev = input_dev
            self.sensor = self.Adafruit_AMG88xx(
                address=self.i2c_address,
                busnum=self.i2c_bus)
            time.sleep(0.1)  # wait for it to boot

            if input_dev.log_level_debug:
                self.logger.setLevel(logging.DEBUG)
            else:
                self.logger.setLevel(logging.INFO)

    def get_measurement(self):
        """ Gets the AMG8833's measurements """
        self.return_dict = measurements_dict.copy()

        pixels = self.sensor.readPixels()

        if self.report:
            self.logger.error("Min Pixel = {0} C".format(min(pixels)))
            self.logger.error("Max Pixel = {0} C".format(max(pixels)))
            self.logger.error("Thermistor = {0} C".format(self.sensor.readThermistor()))

        for meas in self.device_measurements.all():
            if meas.is_enabled:
                self.set_value(meas.channel, pixels[meas.channel])

        if self.save_image:
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            assure_path_exists(PATH_CAMERAS)
            camera_path = assure_path_exists(
                os.path.join(PATH_CAMERAS, '{uid}'.format(uid=self.input_dev.unique_id)))
            filename = 'Still-{uid}-{ts}.jpg'.format(
                uid=self.input_dev.unique_id,
                ts=timestamp).replace(" ", "_")
            save_path = assure_path_exists(os.path.join(camera_path, 'thermal'))
            assure_path_exists(save_path)
            path_file = os.path.join(save_path, filename)
            generate_thermal_image_from_pixels(
                pixels,
                self.nx,
                self.ny,
                path_file,
                scale=self.scale,
                temp_min=self.temp_min,
                temp_max=self.temp_max)

        return self.return_dict
