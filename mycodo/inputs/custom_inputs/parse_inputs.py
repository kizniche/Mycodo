# coding=utf-8
import importlib.util
import logging
import timeit
from pprint import pformat

import os

logging.basicConfig(
    format='%(asctime)s %(levelname)s: %(message)s',
    level='INFO')

logger = logging.getLogger("input_parser")

if __name__ == "__main__":
    excluded_files = ['__init__.py', 'dummy_input.py', 'parse_inputs.py', '__pycache__']
    input_path = '/var/mycodo-root/mycodo/inputs/custom_inputs'
    real_path = os.path.realpath(input_path)

    logger.info("Starting parser")
    logger.info("")

    startup_timer = timeit.default_timer()

    dict_inputs = {}

    for each_file in os.listdir(real_path):
        if each_file not in excluded_files:

            full_path = "{}/{}".format(real_path, each_file)
            logger.info("Found input module: {}".format(full_path))

            spec = importlib.util.spec_from_file_location('module.name', full_path)
            input_custom = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(input_custom)

            logger.info("Module name: {}".format(input_custom.INPUT_INFORMATION['unique_name_input']))

            # Populate dictionary of input information
            if input_custom.INPUT_INFORMATION['unique_name_input'] in dict_inputs:
                logger.error("Error: Cannot add input modules because it does not have a unique name: {name}".format(
                    name=input_custom.INPUT_INFORMATION['unique_name_input']))
            else:
                dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']] = {}

            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['common_name_input'] = \
                input_custom.INPUT_INFORMATION['common_name_input']
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['common_name_measurements'] = \
                input_custom.INPUT_INFORMATION['common_name_measurements']
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['unique_name_measurements'] = \
                input_custom.INPUT_INFORMATION['unique_name_measurements']
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['dependencies_pypi'] = \
                input_custom.INPUT_INFORMATION['dependencies_pypi']
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['dependencies_github'] = \
                input_custom.INPUT_INFORMATION['dependencies_github']
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['interface'] = \
                input_custom.INPUT_INFORMATION['interface']

            # I2C
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['location'] = \
                input_custom.INPUT_INFORMATION['location']

            # UART
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['serial_default_baud_rate'] = \
                input_custom.INPUT_INFORMATION['serial_default_baud_rate']
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['pin_cs'] = \
                input_custom.INPUT_INFORMATION['pin_cs']
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['pin_miso'] = \
                input_custom.INPUT_INFORMATION['pin_miso']
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['pin_mosi'] = \
                input_custom.INPUT_INFORMATION['pin_mosi']
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['pin_clock'] = \
                input_custom.INPUT_INFORMATION['pin_clock']

            # Misc
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['resolution'] = \
                input_custom.INPUT_INFORMATION['resolution']
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['resolution_2'] = \
                input_custom.INPUT_INFORMATION['resolution_2']
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['sensitivity'] = \
                input_custom.INPUT_INFORMATION['sensitivity']
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['thermocouple_type'] = \
                input_custom.INPUT_INFORMATION['thermocouple_type']

            logger.info("")

    run_time = timeit.default_timer() - startup_timer
    logger.info("Run time: {time:.3f} seconds".format(time=run_time))
    logger.info("")

    logger.info("Parsed Input Information:\n{}".format(pformat(dict_inputs)))
