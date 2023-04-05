# -*- coding: utf-8 -*-
import logging
import os
import sys

sys.path.append(
    os.path.abspath(os.path.join(
        os.path.dirname(__file__), os.path.pardir) + '/..'))

from mycodo.config import (CAMERA_INFO, DEPENDENCIES_GENERAL,
                           DEPENDENCY_LOG_FILE, FUNCTION_INFO,
                           INSTALL_DIRECTORY, METHOD_INFO)
from mycodo.databases.models import (Actions, Camera, Conditional,
                                     CustomController, EnergyUsage, Function,
                                     Input, Method, Output, Trigger, Widget)
from mycodo.mycodo_flask.utils.utils_general import return_dependencies
from mycodo.utils.actions import parse_action_information
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.functions import parse_function_information
from mycodo.utils.inputs import parse_input_information
from mycodo.utils.outputs import parse_output_information
from mycodo.utils.system_pi import cmd_output
from mycodo.utils.widgets import parse_widget_information

logger = logging.getLogger("mycodo.update_dependencies")


def get_installed_apt_dependencies():
    met_deps = []

    list_dependencies = [
        parse_function_information(),
        parse_action_information(),
        parse_input_information(),
        parse_output_information(),
        parse_widget_information(),
        CAMERA_INFO,
        FUNCTION_INFO,
        METHOD_INFO,
        DEPENDENCIES_GENERAL
    ]

    for each_section in list_dependencies:
        for device_type in each_section:
            if 'dependencies_module' in each_section[device_type]:
                dep_mod = each_section[device_type]['dependencies_module']
                for (install_type, package, install_id) in dep_mod:
                    if install_type == 'apt':
                        start = "dpkg-query -W -f='${Status}'"
                        end = '2>/dev/null | grep -c "ok installed"'
                        cmd = f"{start} {package} {end}"
                        _, _, status = cmd_output(cmd, user='root')
                        if not status and install_id not in met_deps:
                            met_deps.append(install_id)

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

    method = db_retrieve_table_daemon(Method)
    for each_dev in method:
        if each_dev.method_type not in devices:
            devices.append(each_dev.method_type)

    function = db_retrieve_table_daemon(Function)
    for each_dev in function:
        if each_dev.function_type not in devices:
            devices.append(each_dev.function_type)
    
    conditional = db_retrieve_table_daemon(Conditional, entry='first')
    if conditional and 'conditional_conditional' not in devices:
        devices.append('conditional_conditional')

    trigger = db_retrieve_table_daemon(Trigger)
    for each_dev in trigger:
        if each_dev.trigger_type not in devices:
            devices.append(each_dev.trigger_type)

    actions = db_retrieve_table_daemon(Actions)
    for each_dev in actions:
        if each_dev.action_type not in devices:
            devices.append(each_dev.action_type)

    custom = db_retrieve_table_daemon(CustomController)
    for each_dev in custom:
        if each_dev.device not in devices:
            devices.append(each_dev.device)

    widget = db_retrieve_table_daemon(Widget)
    for each_dev in widget:
        if each_dev.graph_type not in devices:
            devices.append(each_dev.graph_type)

    energy_usage = db_retrieve_table_daemon(EnergyUsage)
    for each_dev in energy_usage:
        if 'highstock' not in devices:
            devices.append('highstock')

    if devices:
        logger.info(f"Checking dependencies for installed devices: {devices}")

        for each_device in devices:
            device_unmet_dependencies, _, _ = return_dependencies(each_device)
            for each_dep in device_unmet_dependencies:
                if each_dep not in dependencies:
                    dependencies.append(each_dep)

    if dependencies:
        for each_dep in dependencies:
            logger.info(f"Installing: {each_dep[0]}")
            if each_dep[2] == 'bash-commands':
                for each_command in each_dep[1]:
                    command = f"{each_command} | ts '[%Y-%m-%d %H:%M:%S]' >> {DEPENDENCY_LOG_FILE} 2>&1"
                    logger.info(f"Executing command: {command}")
                    cmd_out, cmd_err, cmd_status = cmd_output(
                        command, timeout=600, cwd="/tmp")
                    ret_list = []
                    if cmd_out != b"":
                        ret_list.append(f"out: {cmd_out}")
                    if cmd_err != b"":
                        ret_list.append(f"error: {cmd_err}")
                    if cmd_status is not None:
                        ret_list.append(f"status: {cmd_status}")
                    if ret_list:
                        logger.info(f"Command returned: {', '.join(ret_list)}")
            else:
                install_cmd = f"{INSTALL_DIRECTORY}/mycodo/scripts/dependencies.sh {each_dep[1]}"
                output, err, stat = cmd_output(install_cmd, timeout=3600, user='root')
                if output:
                    formatted_output = output.decode("utf-8").replace('\\n', '\n')
                    logger.info(formatted_output)

    # Check apt dependencies
    logger.info("Checking for updates to apt dependencies...")
    installed_apt_deps = get_installed_apt_dependencies()
    apt_deps = " ".join(installed_apt_deps)

    if apt_deps:
        update_cmd = f'apt-get install -y {apt_deps}'
        output, err, stat = cmd_output(update_cmd, user='root')
        formatted_output = output.decode("utf-8").replace('\\n', '\n')
        logger.info(formatted_output)
