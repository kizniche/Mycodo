# coding=utf-8
import time
from collections import OrderedDict
from datetime import datetime

import copy
import os

from mycodo.config import PATH_CAMERAS
from mycodo.inputs.base_input import AbstractInput
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
    'input_library': 'Adafruit_AMG88xx/Pillow/colour',
    'measurements_name': '8x8 Temperature Grid',
    'measurements_dict': measurements_dict,
    'measurements_rescale': True,
    'scale_from_min': 0.0,
    'scale_from_max': 5.0,

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('apt', 'libjpeg-dev', 'libjpeg-dev'),
        ('apt', 'zlib1g-dev', 'zlib1g-dev'),
        ('pip-pypi', 'colour', 'colour==0.1.5'),
        ('pip-pypi', 'PIL', 'Pillow==8.1.2'),
        ('pip-pypi', 'Adafruit_AMG88xx', 'git+https://github.com/adafruit/Adafruit_AMG88xx_python.git')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x69', '0x68'],
    'i2c_address_editable': False,
}


class InputModule(AbstractInput):
    """A sensor support class that monitors the AMG8833's temperature."""

    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None
        self.save_image = False
        self.temp_max = None
        self.temp_min = None
        self.report = False
        self.scale = 2
        self.nx = 8
        self.ny = 8

        if not testing:
            self.try_initialize()

    def initialize(self):
        from Adafruit_AMG88xx import Adafruit_AMG88xx

        self.sensor = Adafruit_AMG88xx(
            address=int(str(self.input_dev.i2c_location), 16),
            busnum=self.input_dev.i2c_bus)
        time.sleep(0.1)  # wait for it to boot

    def get_measurement(self):
        """Gets the AMG8833's measurements."""
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        pixels = self.sensor.readPixels()

        if self.report:
            self.logger.error("Min Pixel = {0} C".format(min(pixels)))
            self.logger.error("Max Pixel = {0} C".format(max(pixels)))
            self.logger.error("Thermistor = {0} C".format(self.sensor.readThermistor()))

        for channel in self.channels_measurement:
            self.value_set(channel, pixels[channel])

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
