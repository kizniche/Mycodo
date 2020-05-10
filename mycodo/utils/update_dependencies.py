# -*- coding: utf-8 -*-
import importlib
import logging
import sys

import os

sys.path.append(
    os.path.abspath(os.path.join(
        os.path.dirname(__file__), os.path.pardir) + '/..'))

from mycodo.config import CALIBRATION_INFO
from mycodo.config import CAMERA_INFO
from mycodo.config import FUNCTION_ACTION_INFO
from mycodo.config import FUNCTION_INFO
from mycodo.config import INSTALL_DIRECTORY
from mycodo.config import LCD_INFO
from mycodo.config import MATH_INFO
from mycodo.config import METHOD_INFO
from mycodo.databases.models import Actions
from mycodo.databases.models import Camera
from mycodo.databases.models import CustomController
from mycodo.databases.models import Function
from mycodo.databases.models import Input
from mycodo.databases.models import LCD
from mycodo.databases.models import Math
from mycodo.databases.models import Method
from mycodo.databases.models import Output
from mycodo.mycodo_flask.utils.utils_general import return_dependencies
from mycodo.utils.controllers import parse_controller_information
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.outputs import parse_output_information
from mycodo.utils.inputs import parse_input_information
from mycodo.utils.system_pi import cmd_output

logger = logging.getLogger("mycodo.update_dependencies")


def get_installed_dependencies():
    met_deps = []

    list_dependencies = [
        parse_controller_information(),
        parse_input_information(),
        parse_output_information(),
        CALIBRATION_INFO,
        CAMERA_INFO,
        FUNCTION_ACTION_INFO,
        FUNCTION_INFO,
        LCD_INFO,
        MATH_INFO,
        METHOD_INFO,
    ]

    for each_section in list_dependencies:
        for device_type in each_section:
            if 'dependencies_module' in each_section[device_type]:
                dep_mod = each_section[device_type]['dependencies_module']
                for (install_type, package, install_id) in dep_mod:
                    entry = '{0} {1}'.format(install_type, install_id)
                    if install_type in ['pip-pypi', 'pip-git']:
                        try:
                            module = importlib.util.find_spec(package)
                            if module is not None and entry not in met_deps:
                                met_deps.append(entry)
                        except Exception:
                            logger.error(
                                'Exception checking python dependency: '
                                '{dep}'.format(dep=package))
                    elif install_type == 'apt':
                        cmd = 'dpkg -l {}'.format(package)
                        _, _, status = cmd_output(cmd, user='root')
                        if not status and entry not in met_deps:
                            met_deps.append(entry)

    return met_deps


if __name__ == "__main__":
    dependencies = []
    devices = []

    input_dev = db_retrieve_table_daemon(Input)
    for each_dev in input_dev:
        if each_dev.device not in devices:
            devices.append(each_dev.device)

    output = db_retrieve_table_daemon(Output)
    for each_dev in output:
        if each_dev.output_type not in devices:
            devices.append(each_dev.output_type)

    camera = db_retrieve_table_daemon(Camera)
    for each_dev in camera:
        if each_dev.library not in devices:
            devices.append(each_dev.library)

    lcd = db_retrieve_table_daemon(LCD)
    for each_dev in lcd:
        if each_dev.lcd_type not in devices:
            devices.append(each_dev.lcd_type)

    math = db_retrieve_table_daemon(Math)
    for each_dev in math:
        if each_dev.math_type not in devices:
            devices.append(each_dev.math_type)

    method = db_retrieve_table_daemon(Method)
    for each_dev in method:
        if each_dev.method_type not in devices:
            devices.append(each_dev.method_type)

    function = db_retrieve_table_daemon(Function)
    for each_dev in function:
        if each_dev.function_type not in devices:
            devices.append(each_dev.function_type)

    actions = db_retrieve_table_daemon(Actions)
    for each_dev in actions:
        if each_dev.action_type not in devices:
            devices.append(each_dev.action_type)

    custom = db_retrieve_table_daemon(CustomController)
    for each_dev in custom:
        if each_dev.device not in devices:
            devices.append(each_dev.device)

    for each_device in devices:
        device_unmet_dependencies, _ = return_dependencies(each_device)
        for each_dep in device_unmet_dependencies:
            if each_dep not in dependencies:
                dependencies.append(each_dep)

    if dependencies:
        print("Unmet dependencies found: {}".format(dependencies))

        # Install unmet dependencies
        for each_dep in dependencies:
            intsall_cmd = "{pth}/mycodo/scripts/dependencies.sh {dep}".format(
                pth=INSTALL_DIRECTORY,
                dep=each_dep[1])
            output, err, stat = cmd_output(intsall_cmd, user='root')
            formatted_output = output.decode("utf-8").replace('\\n', '\n')
            print("{}".format(formatted_output))

    # Update installed dependencies
    installed_deps = get_installed_dependencies()
    apt_deps = ''
    for each_dep in installed_deps:
        if each_dep.split(' ')[0] == 'apt':
            apt_deps += ' {}'.format(each_dep.split(' ')[1])

    if apt_deps:
        update_cmd = 'apt-get install -y {dep}'.format(
            home=INSTALL_DIRECTORY, dep=apt_deps)
        output, err, stat = cmd_output(update_cmd, user='root')
        formatted_output = output.decode("utf-8").replace('\\n', '\n')
        print("{}".format(formatted_output))

    tmp_req_file = '{home}/install/requirements-generated.txt'.format(home=INSTALL_DIRECTORY)
    with open(tmp_req_file, "w") as f:
        for each_dep in installed_deps:
            if each_dep.split(' ')[0] == 'pip-pypi':
                f.write('{dep}\n'.format(dep=each_dep.split(' ')[1]))
            elif each_dep.split(' ')[0] == 'pip-git':
                f.write('-e {dep}\n'.format(dep=each_dep.split(' ')[1]))

    pip_req_update = '{home}/env/bin/pip install --upgrade -r {home}/install/requirements-generated.txt'.format(
        home=INSTALL_DIRECTORY)
    output, err, stat = cmd_output(pip_req_update, user='root')
    formatted_output = output.decode("utf-8").replace('\\n', '\n')
    print("{}".format(formatted_output))
    os.remove(tmp_req_file)
