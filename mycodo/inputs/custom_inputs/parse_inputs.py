# coding=utf-8
import importlib.util
import logging

import os

logger = logging.getLogger(__name__)

input_path = '/var/mycodo-root/mycodo/inputs/custom_inputs'
real_path = os.path.realpath(input_path)

if __name__ == "__main__":
    print("Starting parser\n")

    for each_file in os.listdir(real_path):
        if each_file not in ['__init__.py', 'dummy_input.py', 'parse_inputs.py', '__pycache__']:

            full_path = "{}/{}".format(real_path, each_file)
            print("File path: {}".format(full_path))

            spec = importlib.util.spec_from_file_location('module.name', full_path)
            foo = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(foo)

            print(foo.INPUT_INFORMATION['common_name_input'])

            print()
