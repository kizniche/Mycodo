# coding=utf-8
# Made from commit https://github.com/David00/rpi-power-monitor/commit/04c88ec8a1b08afdbbc6567e98f0f2f100bc2749
# License: GPLv3
import copy
from collections import OrderedDict
from datetime import datetime
from math import sqrt

from mycodo.inputs.base_input import AbstractInput

# Measurements
measurements_dict = OrderedDict()
measurements_dict[0] = {
    'measurement': 'electrical_potential',
    'unit': 'V'
}
channel = 1
for ct in range(1, 7):
    measurements_dict[channel] = {
        'measurement': 'power',
        'unit': 'W',
        'name': f'CT{ct}'
    }
    measurements_dict[channel + 1] = {
        'measurement': 'electrical_current',
        'unit': 'A',
        'name': f'CT{ct}'
    }
    measurements_dict[channel + 2] = {
        'measurement': 'power_factor',
        'unit': 'unitless',
        'name': f'CT{ct}'
    }
    channel += 3

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'input_rpi_power_monitor',
    'input_manufacturer': 'Power Monitor',
    'input_name': 'RPi 6-Channel Power Monitor (v0.1.0)',
    'input_name_short': 'RPi Power Monitor v0.1.0',
    'input_library': 'rpi-power-monitor',
    'measurements_name': 'AC Voltage, Power, Current, Power Factor',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://github.com/David00/rpi-power-monitor',
    'url_product_purchase': 'https://power-monitor.dalbrecht.tech/',
    'measurements_use_same_timestamp': True,

    'message': "See https://github.com/David00/rpi-power-monitor/wiki/Calibrating-for-Accuracy for calibration procedures.",

    'options_enabled': [
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'rpi_power_monitor', 'git+https://github.com/kizniche/rpi-power-monitor.git')
    ],

    'custom_options': [
        {
            'id': 'grid_voltage',
            'type': 'float',
            'default_value': 124.2,
            'required': True,
            'name': 'Grid Voltage',
            'phrase': 'The AC voltage measured at the outlet'
        },
        {
            'id': 'transformer_voltage',
            'type': 'float',
            'default_value': 10.2,
            'required': True,
            'name': 'Transformer Voltage',
            'phrase': 'The AC voltage measured at the barrel plug of the 9 VAC transformer'
        },
        {
            'id': 'ct1_phase_correction',
            'type': 'float',
            'default_value': 1.0,
            'required': True,
            'name': 'CT1 Phase Correction',
            'phrase': 'The phase correction value for CT1'
        },
        {
            'id': 'ct2_phase_correction',
            'type': 'float',
            'default_value': 1.0,
            'required': True,
            'name': 'CT2 Phase Correction',
            'phrase': 'The phase correction value for CT2'
        },
        {
            'id': 'ct3_phase_correction',
            'type': 'float',
            'default_value': 1.0,
            'required': True,
            'name': 'CT3 Phase Correction',
            'phrase': 'The phase correction value for CT3'
        },
        {
            'id': 'ct4_phase_correction',
            'type': 'float',
            'default_value': 1.0,
            'required': True,
            'name': 'CT4 Phase Correction',
            'phrase': 'The phase correction value for CT4'
        },
        {
            'id': 'ct5_phase_correction',
            'type': 'float',
            'default_value': 1.0,
            'required': True,
            'name': 'CT5 Phase Correction',
            'phrase': 'The phase correction value for CT5'
        },
        {
            'id': 'ct6_phase_correction',
            'type': 'float',
            'default_value': 1.0,
            'required': True,
            'name': 'CT6 Phase Correction',
            'phrase': 'The phase correction value for CT6'
        },
        {
            'id': 'ct1_accuracy_calibration',
            'type': 'float',
            'default_value': 1.0,
            'required': True,
            'name': 'CT1 Accuracy Calibration',
            'phrase': 'The accuracy calibration value for CT1'
        },
        {
            'id': 'ct2_accuracy_calibration',
            'type': 'float',
            'default_value': 1.0,
            'required': True,
            'name': 'CT2 Accuracy Calibration',
            'phrase': 'The accuracy calibration value for CT2'
        },
        {
            'id': 'ct3_accuracy_calibration',
            'type': 'float',
            'default_value': 1.0,
            'required': True,
            'name': 'CT3 Accuracy Calibration',
            'phrase': 'The accuracy calibration value for CT3'
        },
        {
            'id': 'ct4_accuracy_calibration',
            'type': 'float',
            'default_value': 1.0,
            'required': True,
            'name': 'CT4 Accuracy Calibration',
            'phrase': 'The accuracy calibration value for CT4'
        },
        {
            'id': 'ct5_accuracy_calibration',
            'type': 'float',
            'default_value': 1.0,
            'required': True,
            'name': 'CT5 Accuracy Calibration',
            'phrase': 'The accuracy calibration value for CT5'
        },
        {
            'id': 'ct6_accuracy_calibration',
            'type': 'float',
            'default_value': 1.0,
            'required': True,
            'name': 'CT6 Accuracy Calibration',
            'phrase': 'The accuracy calibration value for CT6'
        },
        {
            'id': 'ac_accuracy_calibration',
            'type': 'float',
            'default_value': 1.0,
            'required': True,
            'name': 'AC Accuracy Calibration',
            'phrase': 'The accuracy calibration value for AC'
        }
    ]
}

class InputModule(AbstractInput):
    """ Input module to read the Raspberry Pi Power Monitor HAT """
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None

        self.grid_voltage = None
        self.transformer_voltage = None

        self.ct1_phase_correction = None
        self.ct2_phase_correction = None
        self.ct3_phase_correction = None
        self.ct4_phase_correction = None
        self.ct5_phase_correction = None
        self.ct6_phase_correction = None

        self.ct1_accuracy_calibration = None
        self.ct2_accuracy_calibration = None
        self.ct3_accuracy_calibration = None
        self.ct4_accuracy_calibration = None
        self.ct5_accuracy_calibration = None
        self.ct6_accuracy_calibration = None
        self.ac_accuracy_calibration = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.try_initialize()

    def initialize(self):
        from rpi_power_monitor import power_monitor

        phase_correction = {
            'ct1': self.ct1_phase_correction,
            'ct2': self.ct2_phase_correction,
            'ct3': self.ct3_phase_correction,
            'ct4': self.ct4_phase_correction,
            'ct5': self.ct5_phase_correction,
            'ct6': self.ct6_phase_correction,
        }

        accuracy_calibration = {
            'ct1': self.ct1_accuracy_calibration,
            'ct2': self.ct2_accuracy_calibration,
            'ct3': self.ct3_accuracy_calibration,
            'ct4': self.ct4_accuracy_calibration,
            'ct5': self.ct5_accuracy_calibration,
            'ct6': self.ct6_accuracy_calibration,
            'AC': self.ac_accuracy_calibration,
        }

        self.sensor = power_monitor.RPiPowerMonitor(
            grid_voltage=self.grid_voltage,
            ac_transformer_output_voltage=self.transformer_voltage,
            ct_phase_correction=phase_correction,
            accuracy_calibration=accuracy_calibration)

    def get_measurement(self):
        self.return_dict = copy.deepcopy(measurements_dict)

        board_voltage = self.sensor.get_board_voltage()

        samples = self.sensor.collect_data(2000)

        rebuilt_waves = self.sensor.rebuild_waves(
            samples,
            self.sensor.ct_phase_correction['ct1'],
            self.sensor.ct_phase_correction['ct2'],
            self.sensor.ct_phase_correction['ct3'],
            self.sensor.ct_phase_correction['ct4'],
            self.sensor.ct_phase_correction['ct5'],
            self.sensor.ct_phase_correction['ct6'])

        results = self.sensor.calculate_power(rebuilt_waves, board_voltage)

        self.value_set(0, results['voltage'])

        chan = 1
        for ct in range(1, 7):
            self.value_set(chan, results[f'ct{ct}']['power'])
            self.value_set(chan + 1, results[f'ct{ct}']['current'])
            self.value_set(chan + 2, results[f'ct{ct}']['pf'])
            chan += 3

        return self.return_dict
