# -*- coding: utf-8 -*-
#
#  controllers.py - Mycodo core utils for controllers
#
#  Copyright (C) 2018  Kyle T. Gabriel
#
#  This file is part of Mycodo
#
#  Mycodo is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Mycodo is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Mycodo. If not, see <http://www.gnu.org/licenses/>.
#
#  Contact at kylegabriel.com


import logging

import os

from mycodo.config import PATH_CONTROLLERS
from mycodo.config import PATH_CONTROLLERS_CUSTOM
from mycodo.utils.modules import load_module_from_file

logger = logging.getLogger("mycodo.utils.controllers")


def parse_controller_information():
    """Parses the variables assigned in each Controller and return a dictionary of IDs and values"""
    def dict_has_value(dict_inp, controller_cus, key):
        if (key in controller_cus.CONTROLLER_INFORMATION and
                (controller_cus.CONTROLLER_INFORMATION[key] or
                 controller_cus.CONTROLLER_INFORMATION[key] == 0)):
            dict_inp[controller_cus.CONTROLLER_INFORMATION['controller_name_unique']][key] = \
                controller_cus.CONTROLLER_INFORMATION[key]
        return dict_inp

    excluded_files = [
        '__init__.py', '__pycache__', 'base_controller.py',
        'custom_controllers', 'examples', 'scripts', 'tmp_controllers',
        'sensorutils.py', 'controller_conditional.py', 'controller_input.py',
        'controller_lcd.py', 'controller_math.py', 'controller_output.py',
        'controller_pid.py', 'controller_trigger.py'
    ]

    controller_paths = [PATH_CONTROLLERS, PATH_CONTROLLERS_CUSTOM]

    dict_controllers = {}

    for each_path in controller_paths:

        real_path = os.path.realpath(each_path)

        for each_file in os.listdir(real_path):
            skip_file = False

            if each_file in excluded_files:
                skip_file = True

            if not skip_file:
                full_path = "{}/{}".format(real_path, each_file)
                controller_custom = load_module_from_file(full_path, 'controllers')

                if not hasattr(controller_custom, 'CONTROLLER_INFORMATION'):
                    skip_file = True

            if not skip_file:
                # logger.info("Found controller: {}, {}".format(
                #     controller_custom.CONTROLLER_INFORMATION['controller_name_unique'],
                #     full_path))

                # Populate dictionary of controller information
                if controller_custom.CONTROLLER_INFORMATION['controller_name_unique'] in dict_controllers:
                    logger.error("Error: Cannot add controller modules because it does not have a unique name: {name}".format(
                        name=controller_custom.CONTROLLER_INFORMATION['controller_name_unique']))
                else:
                    dict_controllers[controller_custom.CONTROLLER_INFORMATION['controller_name_unique']] = {}

                dict_controllers[controller_custom.CONTROLLER_INFORMATION['controller_name_unique']]['file_path'] = full_path

                dict_controllers = dict_has_value(dict_controllers, controller_custom, 'controller_name')
                dict_controllers = dict_has_value(dict_controllers, controller_custom, 'message')
                dict_controllers = dict_has_value(dict_controllers, controller_custom, 'options_enabled')
                dict_controllers = dict_has_value(dict_controllers, controller_custom, 'options_disabled')

                # Dependencies
                dict_controllers = dict_has_value(dict_controllers, controller_custom, 'dependencies_module')

                dict_controllers = dict_has_value(dict_controllers, controller_custom, 'custom_options')

    return dict_controllers
