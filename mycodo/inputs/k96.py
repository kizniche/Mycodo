# coding=utf-8
import copy
import time

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import calculate_altitude
from mycodo.inputs.sensorutils import calculate_dewpoint
from mycodo.inputs.sensorutils import calculate_vapor_pressure_deficit
from mycodo.inputs.sensorutils import convert_from_x_to_y_unit

# Measurements
measurements_dict = {
    0: {
        'measurement': 'methane',
        'unit': 'unitless',
        'name': 'LPL_signal',
        'command': 'FE 44 01 80 04 28 E7',
        'convert': 1
    },
    1: {
        'measurement': 'humidity',
        'unit': 'unitless',
        'name': 'MPL_signal',
        'command': 'FE 44 03 60 04 C0 E7',
        'convert': 1
    },
    2: {
        'measurement': 'co2',
        'unit': 'unitless',
        'name': 'SPL_signal',
        'command': 'FE 44 01 90 04 25 27',
        'convert': 1
    },
    3: {
        'measurement': 'methane',
        'unit': 'ppm',
        'name': 'LPL_uflt_Conc',
        'command': 'FE 44 04 2A 02 C6 44',
        'convert': 0.1
    },
    4: {
        'measurement': 'humidity',
        'unit': 'ppm',
        'name': 'MPL_uflt_Conc',
        'command': 'FE 44 03 8A 02 0F 85',
        'convert': 1
    },
    5: {
        'measurement': 'co2',
        'unit': 'ppm',
        'name': 'SPL_uflt_Conc',
        'command': 'FE 44 04 8A 02 BE 44',
        'convert': 1
    },
    6: {
        'measurement': 'pressure',
        'unit': 'hPa',
        'name': 'BME_Pres',
        'command': 'FE 44 01 D0 02 94 E5',
        'convert': 0.1
    },
    7: {
        'measurement': 'humidity',
        'unit': 'percent',
        'name': 'BME_RH',
        'command': 'FE 44 01 F0 02 8D 25',
        'convert': 0.01
    },
    8: {
        'measurement': 'temperature',
        'unit': 'C',
        'name': 'BME_Temp',
        'command': 'FE 44 01 F8 02 8A E5',
        'convert': 0.01
    },
    9: {
        'measurement': 'temperature',
        'unit': 'C',
        'name': 'NTC0_Temp',
        'command': 'FE 44 01 B8 03 7A E5',
        'convert': (1/256)/100
    },
    10: {
        'measurement': 'temperature',
        'unit': 'C',
        'name': 'NTC1_Temp',
        'command': 'FE 44 01 C0 03 58 E5',
        'convert': (1/256)/100
    },
    11: {
        'measurement': 'dewpoint',
        'unit': 'C'
    },
    12: {
        'measurement': 'altitude',
        'unit': 'm'
    },
    13: {
        'measurement': 'vapor_pressure_deficit',
        'unit': 'Pa'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'K96',
    'input_manufacturer': 'Senseair',
    'input_name': 'K96',
    'input_library': 'Serial',
    'measurements_name': 'Methane/Moisture/CO2/Pressure/Humidity/Temperature',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'measurements_select',
        'uart_location',
        'uart_baud_rate',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'interfaces': ['UART'],
    'uart_location': '/dev/ttyS0',
    'uart_baud_rate': 115200
}

class InputModule(AbstractInput):
    """
    A sensor support class that measures the sensor
    """
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None

        if not testing:
            self.try_initialize()

    def initialize(self):
        import serial

        self.sensor = serial.Serial(
            self.input_dev.uart_location,
            baudrate=self.input_dev.baud_rate,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_TWO,
            timeout=0.5)

    def get_measurement(self):
        """Gets the measurements"""
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        for channel, params in measurements_dict.items():
            value = None

            if channel == 11 and self.value_get(8) and self.value_get(7):
                value = calculate_dewpoint(
                    self.value_get(8), self.value_get(7))
            elif channel == 12 and self.value_get(6):
                value = calculate_altitude(
                    convert_from_x_to_y_unit('hPa', 'Pa', self.value_get(6)))
            elif channel == 13 and self.value_get(8) and self.value_get(7):
                value = calculate_vapor_pressure_deficit(
                    self.value_get(8), self.value_get(7))
            else:
                try:
                    cmd = params['command']
                    cmd_write = bytearray.fromhex(cmd)
                    self.sensor.flushOutput()
                    self.sensor.flushInput()
                    time.sleep(0.1)
                    self.sensor.write(cmd_write)
                    time.sleep(0.1)
                    read = self.sensor.read(7)

                    if len(read) > 1:
                        if cmd[12:14] == '02':
                            value = int(f'0x{read[3]:0>2x}{read[4]:0>2x}', 16)
                            if value >= (2 ** 16) / 2:
                                value -= (2 ** 16)
                        elif cmd[12:14] == '03':
                            value = int(f'0x{read[3]:0>2x}{read[4]:0>2x}{read[5]:0>2x}', 16)
                            if value >= (2 ** 24) / 2:
                                value -= (2 ** 24)
                        else:
                            value = int(f'0x{read[3]:0>2x}{read[4]:0>2x}{read[5]:0>2x}{read[6]:0>2x}', 16)
                            if value >= (2 ** 32) / 2:
                                value -= (2 ** 32)

                        value = value * params['convert']
                        value = round(value, 2)
                except Exception as err:
                    self.logger.error(f"Error: {err}")

            if self.is_enabled(channel) and value is not None:
                self.value_set(channel, value)

        return self.return_dict
