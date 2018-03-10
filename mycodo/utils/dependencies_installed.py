# -*- coding: utf-8 -*-
import importlib
import logging
import sys

import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir) + '/..'))
from mycodo.config import DEVICE_INFO
from mycodo.config import MATH_INFO
from mycodo.config import METHOD_INFO

logger = logging.getLogger("mycodo.dependencies_installed")


def get_installed_dependencies():
    met_deps = []

    list_dependencies = [
        DEVICE_INFO,
        MATH_INFO,
        METHOD_INFO
    ]
    for each_section in list_dependencies:
        for device_type in each_section:
            for each_device, each_dict in each_section[device_type].items():
                if each_device == 'py-dependencies':
                    for each_dep in each_dict:
                        try:
                            module = importlib.util.find_spec(each_dep)
                            if module is not None:
                                if each_dep not in met_deps:
                                    met_deps.append(each_dep)
                        except Exception:
                            logger.error(
                                'Exception while checking python dependency: '
                                '{dep}'.format(dep=each_dep))

    if os.path.exists('/usr/local/bin/gpio'):
        met_deps.append('wiringpi')

    return (',').join(met_deps)


if __name__ == "__main__":
    print(get_installed_dependencies())
