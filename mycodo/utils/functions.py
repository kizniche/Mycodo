# -*- coding: utf-8 -*-
#
#  functions.py - Mycodo core utils for functions
#
#  Copyright (C) 2015-2020 Kyle T. Gabriel <mycodo@kylegabriel.com>
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

from mycodo.config import PATH_FUNCTIONS
from mycodo.config import PATH_FUNCTIONS_CUSTOM
from mycodo.utils.modules import load_module_from_file

logger = logging.getLogger("mycodo.utils.functions")


def parse_function_information(exclude_custom=False):
    """Parses the variables assigned in each Function and return a dictionary of IDs and values."""
    def dict_has_value(dict_inp, controller_cus, key):
        if (key in controller_cus.FUNCTION_INFORMATION and
                (controller_cus.FUNCTION_INFORMATION[key] or
                 controller_cus.FUNCTION_INFORMATION[key] == 0)):
            dict_inp[controller_cus.FUNCTION_INFORMATION['function_name_unique']][key] = \
                controller_cus.FUNCTION_INFORMATION[key]
        return dict_inp

    excluded_files = [
        '__init__.py', '__pycache__', 'base_function.py',
        'custom_functions', 'examples', 'scripts', 'tmp_functions'
    ]

    function_paths = [PATH_FUNCTIONS]

    if not exclude_custom:
        function_paths.append(PATH_FUNCTIONS_CUSTOM)

    dict_controllers = {}

    for each_path in function_paths:

        real_path = os.path.realpath(each_path)

        for each_file in os.listdir(real_path):
            if each_file in excluded_files:
                continue

            full_path = "{}/{}".format(real_path, each_file)
            function_custom, status = load_module_from_file(full_path, 'functions')

            if not function_custom or not hasattr(function_custom, 'FUNCTION_INFORMATION'):
                continue

            # Populate dictionary of function information
            if function_custom.FUNCTION_INFORMATION['function_name_unique'] in dict_controllers:
                logger.error(
                    "Error: Cannot add controller modules because it does not have a unique name: {name}".format(
                        name=function_custom.FUNCTION_INFORMATION['function_name_unique']))
            else:
                dict_controllers[function_custom.FUNCTION_INFORMATION['function_name_unique']] = {}

            dict_controllers[function_custom.FUNCTION_INFORMATION['function_name_unique']]['file_path'] = full_path

            dict_controllers = dict_has_value(dict_controllers, function_custom, 'function_name')
            dict_controllers = dict_has_value(dict_controllers, function_custom, 'function_name_short')
            dict_controllers = dict_has_value(dict_controllers, function_custom, 'function_manufacturer')
            dict_controllers = dict_has_value(dict_controllers, function_custom, 'measurements_dict')
            dict_controllers = dict_has_value(dict_controllers, function_custom, 'channels_dict')
            dict_controllers = dict_has_value(dict_controllers, function_custom, 'measurements_variable_amount')
            dict_controllers = dict_has_value(dict_controllers, function_custom, 'channel_quantity_same_as_measurements')
            dict_controllers = dict_has_value(dict_controllers, function_custom, 'enable_channel_unit_select')
            dict_controllers = dict_has_value(dict_controllers, function_custom, 'execute_at_creation')
            dict_controllers = dict_has_value(dict_controllers, function_custom, 'execute_at_modification')
            dict_controllers = dict_has_value(dict_controllers, function_custom, 'modify_settings_without_deactivating')
            dict_controllers = dict_has_value(dict_controllers, function_custom, 'function_status')
            dict_controllers = dict_has_value(dict_controllers, function_custom, 'camera_image')
            dict_controllers = dict_has_value(dict_controllers, function_custom, 'camera_video')
            dict_controllers = dict_has_value(dict_controllers, function_custom, 'camera_stream')
            dict_controllers = dict_has_value(dict_controllers, function_custom, 'message')
            dict_controllers = dict_has_value(dict_controllers, function_custom, 'options_enabled')
            dict_controllers = dict_has_value(dict_controllers, function_custom, 'options_disabled')
            dict_controllers = dict_has_value(dict_controllers, function_custom, 'dependencies_module')
            dict_controllers = dict_has_value(dict_controllers, function_custom, 'dependencies_message')
            dict_controllers = dict_has_value(dict_controllers, function_custom, 'function_actions')
            dict_controllers = dict_has_value(dict_controllers, function_custom, 'custom_options')
            dict_controllers = dict_has_value(dict_controllers, function_custom, 'custom_channel_options')
            dict_controllers = dict_has_value(dict_controllers, function_custom, 'custom_commands_message')
            dict_controllers = dict_has_value(dict_controllers, function_custom, 'custom_commands')

    return dict_controllers
