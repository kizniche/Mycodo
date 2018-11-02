# coding=utf-8
import logging
import time
from collections import OrderedDict
from datetime import datetime

import os

from mycodo.config import PATH_CAMERAS
from mycodo.databases.models import InputMeasurements
from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.image import generate_thermal_image_from_pixels
from mycodo.utils.system_pi import assure_path_exists

# Channels
channels = {}
for each_channel in range(64):
    channels[each_channel] = {}

# Measurements
measurements = {
    'temperature': {
        'C': channels
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'AMG8833',
    'input_manufacturer': 'Panasonic',
    'input_name': 'AMG8833',
    'measurements_name': '8x8 Temperature Grid',
    'measurements_dict': measurements,
    'measurements_convert_enabled': False,
    'measurements_rescale': True,
    'scale_from_min': 0.0,
    'scale_from_max': 5.0,

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'measurements_convert',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('apt', 'libjpeg-dev', 'libjpeg-dev'),
        ('apt', 'zlib1g-dev', 'zlib1g-dev'),
        ('pip-pypi', 'colour', 'colour'),
        ('pip-pypi', 'PIL', 'Pillow'),
        ('pip-pypi', 'w1thermsensor', 'w1thermsensor'),
        ('pip-pypi', 'w1thermsensor', 'w1thermsensor')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x69', '0x68'],
    'i2c_address_editable': False,
}


class InputModule(AbstractInput):
    """ A sensor support class that monitors the AMG8833's temperature """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.amg8833")
        self._measurements = None

        self.save_image = False
        self.temp_max = None
        self.temp_min = None
        self.report = False
        self.scale = 2
        self.nx = 8
        self.ny = 8

        if not testing:
            from Adafruit_AMG88xx import Adafruit_AMG88xx
            self.logger = logging.getLogger(
                "mycodo.ds18b20_{id}".format(id=input_dev.unique_id.split('-')[0]))

            self.input_measurements = db_retrieve_table_daemon(
                InputMeasurements).filter(
                    InputMeasurements.input_id == input_dev.unique_id).all()

            self.Adafruit_AMG88xx = Adafruit_AMG88xx
            self.i2c_address = int(str(input_dev.i2c_location), 16)
            self.i2c_bus = input_dev.i2c_bus
            self.input_dev = input_dev
            self.sensor = self.Adafruit_AMG88xx(address=self.i2c_address,
                                                busnum=self.i2c_bus)
            time.sleep(.1)  # wait for it to boot

    def get_measurement(self):
        """ Gets the AMG8833's measurements """
        self._measurements = None

        pixels_dict = {
            'temperature': {
                'C': OrderedDict()
            }
        }

        pixels = self.sensor.readPixels()

        if self.report:
            self.logger.error("Min Pixel = {0} C".format(min(pixels)))
            self.logger.error("Max Pixel = {0} C".format(max(pixels)))
            self.logger.error("Thermistor = {0} C".format(self.sensor.readThermistor()))

        for meas in self.input_measurements:
            if meas.is_enabled:
                pixels_dict[meas.measurement][meas.unit][meas.channel] = pixels[meas.channel]

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

        if pixels_dict:
            return pixels_dict
