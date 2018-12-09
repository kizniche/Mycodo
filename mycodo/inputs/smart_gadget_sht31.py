# coding=utf-8
import logging
import struct

from mycodo.databases.models import DeviceMeasurements
from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.inputs.sensorutils import calculate_dewpoint
from mycodo.inputs.sensorutils import calculate_vapor_pressure_deficit

# Measurements
measurements_dict = {
    0: {
        'measurement': 'temperature',
        'unit': 'C'
    },
    1: {
        'measurement': 'humidity',
        'unit': 'percent'
    },
    2: {
        'measurement': 'dewpoint',
        'unit': 'C'
    },
    3: {
        'measurement': 'vapor_pressure_deficit',
        'unit': 'Pa'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'SMART_GADGET_SHT31',
    'input_manufacturer': 'Sensorion',
    'input_name': 'SHT31 Smart Gadget',
    'measurements_name': 'Humidity/Temperature',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'bt_location',
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'bluepy', 'bluepy')
    ],

    'interfaces': ['BT'],
    'bt_location': '00:00:00:00:00:00',
    'bt_adapter': '0'
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the Miflora's electrical
    conductivity, moisture, temperature, and light.

    """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.sensor_gadget_sht31")
        self._measurements = None

        self.uuid_humidity_service = '00001234-B38D-4985-720E-0F993A68EE41'
        self.uuid_humidity_char = '00001235-B38D-4985-720E-0F993A68EE41'

        self.uuid_temperature_service = '00002234-B38D-4985-720E-0F993A68EE41'
        self.uuid_temperature_char = '00002235-B38D-4985-720E-0F993A68EE41'

        if not testing:
            from bluepy.btle import UUID, Peripheral
            self.logger = logging.getLogger(
                "mycodo.sensor_gadget_sht31_{id}".format(id=input_dev.unique_id.split('-')[0]))

            self.device_measurements = db_retrieve_table_daemon(
                DeviceMeasurements).filter(
                    DeviceMeasurements.device_id == input_dev.unique_id)

            self.location = input_dev.location
            self.bt_adapter = input_dev.bt_adapter

            self.p = Peripheral(self.location,
                                "random",
                                iface=self.bt_adapter)

    def get_measurement(self):
        """ Gets the light, moisture, and temperature """
        return_dict = measurements_dict.copy()

        sht31_service = self.p.getServiceByUUID(self.uuid_humidity_service)
        ch = sht31_service.getCharacteristics(self.uuid_humidity_char)[0]
        humidity = struct.unpack('<f', ch.read())[0]

        sht31_service = self.p.getServiceByUUID(self.uuid_temperature_service)
        ch = sht31_service.getCharacteristics(self.uuid_temperature_char)[0]
        temperature = struct.unpack('<f', ch.read())[0]

        if self.is_enabled(0):
            return_dict[0]['value'] = temperature

        if self.is_enabled(1):
            return_dict[1]['value'] = humidity

        if (self.is_enabled(2) and
                self.is_enabled(0) and
                self.is_enabled(1)):
            return_dict[2]['value'] = calculate_dewpoint(
                return_dict[0]['value'], return_dict[1]['value'])

        if (self.is_enabled(3) and
                self.is_enabled(0) and
                self.is_enabled(1)):
            return_dict[3]['value'] = calculate_vapor_pressure_deficit(
                return_dict[0]['value'], return_dict[1]['value'])

        return return_dict

    def stop_sensor(self):
        """ Called when sensors are deactivated """
        try:
            self.p.disconnect()
        except Exception as msg:
            self.logger.error("Error: {err}".format(err=msg))
        self.running = False
