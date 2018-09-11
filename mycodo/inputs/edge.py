# coding=utf-8
import logging

from mycodo.inputs.base_input import AbstractInput

# Input information
INPUT_INFORMATION = {
    'unique_name_input': 'EDGE',
    'input_manufacturer': 'Mycodo',
    'common_name_input': 'Edge',
    'common_name_measurements': 'Rising/Falling Edge',
    'unique_name_measurements': ['edge'],  # List of strings
    'dependencies_pip': ['RPi.GPIO'],  # List of strings
    'interfaces': ['GPIO'],  # List of strings
    'options_disabled': ['interface'],
    'options_enabled': ['gpio_location', 'period', 'pre_output'],
}
