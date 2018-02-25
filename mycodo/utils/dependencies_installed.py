# -*- coding: utf-8 -*-
import importlib
import logging
import sys

import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir) + '/..'))
from mycodo.config import MEASUREMENTS

logger = logging.getLogger("mycodo.dependencies_installed")


def get_installed_dependencies():
    met_deps = []
    for device_type in MEASUREMENTS:
        for each_device, each_dict in MEASUREMENTS[device_type].items():
            if each_device == 'py-dependencies':
                for each_dep in each_dict:
                    module = importlib.util.find_spec(each_dep)
                    if module is not None:
                        if each_dep not in met_deps:
                            met_deps.append(each_dep)

    return (',').join(met_deps)


if __name__ == "__main__":
    print(get_installed_dependencies())
