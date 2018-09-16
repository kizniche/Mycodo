# -*- coding: utf-8 -*-
import importlib
import logging
import sys

import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir) + '/..'))

from mycodo.config import MATH_INFO
from mycodo.config import METHOD_INFO
from mycodo.config import OUTPUT_INFO

from mycodo.utils.inputs import parse_input_information

logger = logging.getLogger("mycodo.dependencies_installed")


def get_installed_dependencies():
    met_deps = []

    dict_inputs = parse_input_information()

    list_dependencies = [
        dict_inputs,
        MATH_INFO,
        METHOD_INFO,
        OUTPUT_INFO
    ]
    for each_section in list_dependencies:
        for device_type in each_section:
            for each_device, each_dict in each_section[device_type].items():
                if each_device == 'dependencies_module':
                    for (install_type, py_module, install_id) in each_dict:
                        if install_type == 'pip':
                            try:
                                module = importlib.util.find_spec(py_module)
                                if module is not None:
                                    if (install_type, py_module, install_id) not in met_deps:
                                        met_deps.append(install_id)
                            except Exception:
                                logger.error(
                                    'Exception while checking python dependency: '
                                    '{dep}'.format(dep=install_id))

    return (',').join(met_deps)


if __name__ == "__main__":
    print(get_installed_dependencies())
