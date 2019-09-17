# -*- coding: utf-8 -*-
import importlib
import logging
import sys

import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir) + '/..'))

from mycodo.config import INSTALL_DIRECTORY
from mycodo.config import MATH_INFO
from mycodo.config import METHOD_INFO
from mycodo.config import OUTPUT_INFO

from mycodo.utils.inputs import parse_input_information
from mycodo.utils.system_pi import cmd_output

logger = logging.getLogger("mycodo.update_installed_dependencies")


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
                    for (install_type, package, install_id) in each_dict:
                        entry = '{0} {1}'.format(install_type, install_id)
                        if install_type in ['pip-pypi', 'pip-git']:
                            try:
                                module = importlib.util.find_spec(package)
                                if module is not None and entry not in met_deps:
                                    met_deps.append(entry)
                            except Exception:
                                logger.error(
                                    'Exception while checking python dependency: '
                                    '{dep}'.format(dep=package))
                        elif install_type == 'apt':
                            cmd = 'dpkg -l {}'.format(package)
                            _, _, stat = cmd_output(cmd, user='root')
                            if not stat and entry not in met_deps:
                                met_deps.append(entry)

    return met_deps


if __name__ == "__main__":
    installed_deps = get_installed_dependencies()
    for each_dep in installed_deps:
        if each_dep.split(' ')[0] == 'apt':
            update_cmd = '{home}/mycodo/scripts/dependencies.sh {dep}'.format(
                home=INSTALL_DIRECTORY, dep=each_dep)
            output, err, stat = cmd_output(update_cmd, user='root')
            print("{}".format(output))

    tmp_req_file = '{home}/install/requirements-generated.txt'.format(home=INSTALL_DIRECTORY)
    with open(tmp_req_file, "w") as f:
        for each_dep in installed_deps:
            if each_dep.split(' ')[0] == 'pip-pypi':
                f.write('{dep}\n'.format(dep=each_dep.split(' ')[1]))
            elif each_dep.split(' ')[0] == 'pip-git':
                f.write('-e {dep}\n'.format(dep=each_dep.split(' ')[1]))

    pip_req_update = '{home}/env/bin/pip install --upgrade -r {home}/install/requirements-generated.txt'.format(home=INSTALL_DIRECTORY)
    output, err, stat = cmd_output(pip_req_update, user='root')
    print("{}".format(output))
    os.remove(tmp_req_file)
