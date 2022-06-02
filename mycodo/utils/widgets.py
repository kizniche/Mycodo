# -*- coding: utf-8 -*-
#
#  widgets.py - Mycodo core utils
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

from mycodo.config import PATH_WIDGETS
from mycodo.config import PATH_WIDGETS_CUSTOM
from mycodo.utils.logging_utils import set_log_level
from mycodo.utils.modules import load_module_from_file

logger = logging.getLogger("mycodo.utils.widgets")
logger.setLevel(set_log_level(logging))


def parse_widget_information(exclude_custom=False):
    """Parses the variables assigned in each Widget and return a dictionary of IDs and values."""
    def dict_has_value(dict_inp, widget_cus, key, force_type=None):
        if (key in widget_cus.WIDGET_INFORMATION and
                (widget_cus.WIDGET_INFORMATION[key] or
                 widget_cus.WIDGET_INFORMATION[key] == 0)):
            if force_type == 'list':
                if isinstance(widget_cus.WIDGET_INFORMATION[key], list):
                    dict_inp[widget_cus.WIDGET_INFORMATION['widget_name_unique']][key] = \
                        widget_cus.WIDGET_INFORMATION[key]
                else:
                    dict_inp[widget_cus.WIDGET_INFORMATION['widget_name_unique']][key] = \
                        [widget_cus.WIDGET_INFORMATION[key]]
            else:
                dict_inp[widget_cus.WIDGET_INFORMATION['widget_name_unique']][key] = \
                    widget_cus.WIDGET_INFORMATION[key]
        return dict_inp

    excluded_files = [
        '__init__.py', '__pycache__', 'base_widget.py', 'custom_widgets',
        'examples', 'tmp_widgets'
    ]

    widget_paths = [PATH_WIDGETS]

    if not exclude_custom:
        widget_paths.append(PATH_WIDGETS_CUSTOM)

    dict_widgets = {}

    for each_path in widget_paths:

        real_path = os.path.realpath(each_path)

        for each_file in os.listdir(real_path):
            if each_file in excluded_files:
                continue

            full_path = f"{real_path}/{each_file}"
            widget_custom, status = load_module_from_file(full_path, 'widgets')

            if not widget_custom or not hasattr(widget_custom, 'WIDGET_INFORMATION'):
                continue

            # Populate dictionary of widget information
            if widget_custom.WIDGET_INFORMATION['widget_name_unique'] in dict_widgets:
                logger.error(f"Error: Cannot add widget modules because it does not have "
                             f"a unique name: {widget_custom.WIDGET_INFORMATION['widget_name_unique']}")
            else:
                dict_widgets[widget_custom.WIDGET_INFORMATION['widget_name_unique']] = {}

            dict_widgets[widget_custom.WIDGET_INFORMATION['widget_name_unique']]['file_path'] = full_path

            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'widget_name')
            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'widget_library')
            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'no_class')

            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'widget_height')
            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'widget_width')

            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'listener')
            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'message')

            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'url_datasheet', force_type='list')
            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'url_manufacturer', force_type='list')
            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'url_product_purchase', force_type='list')
            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'url_additional', force_type='list')

            # Dependencies
            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'dependencies_module')
            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'dependencies_message')

            # Which form options to display and whether each option is enabled
            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'options_enabled')
            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'options_disabled')

            # Misc
            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'period')

            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'endpoints')
            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'execute_at_creation')
            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'execute_at_modification')
            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'execute_at_deletion')
            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'generate_page_variables')

            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'custom_options_message')
            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'custom_options')

            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'custom_commands_message')
            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'custom_commands')

            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'widget_dashboard_head')
            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'widget_dashboard_title_bar')
            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'widget_dashboard_body')
            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'widget_dashboard_configure_options')
            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'widget_dashboard_js')
            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'widget_dashboard_js_ready')
            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'widget_dashboard_js_ready_end')

    return dict_widgets
