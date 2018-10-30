# coding=utf-8
import logging

from mycodo.inputs.base_input import AbstractInput

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'EDGE',
    'input_manufacturer': 'Mycodo',
    'input_name': 'Edge',
    'measurements_name': 'Rising/Falling Edge',
    'measurements_dict': ['edge'],
    'options_enabled': ['gpio_location', 'period', 'pre_output'],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'RPi.GPIO', 'RPi.GPIO')
    ],
    'interfaces': ['GPIO']
}
