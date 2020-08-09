# -*- coding: utf-8 -*-
#
#  widgets.py - Mycodo core utils
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

from mycodo.config import PATH_HTML_USER
from mycodo.config import PATH_WIDGETS
from mycodo.config import PATH_WIDGETS_CUSTOM
from mycodo.utils.modules import load_module_from_file
from mycodo.utils.system_pi import assure_path_exists
from mycodo.utils.system_pi import set_user_grp

logger = logging.getLogger("mycodo.utils.widgets")


def generate_widget_html():
    """ Generate all HTML files for all widgets """
    dict_widgets = parse_widget_information()
    assure_path_exists(PATH_HTML_USER)

    for widget_name in dict_widgets:
        try:
            filename_head = "widget_template_{}_head.html".format(widget_name)
            path_head = os.path.join(PATH_HTML_USER, filename_head)
            with open(path_head, 'w') as fw:
                if 'widget_dashboard_head' in dict_widgets[widget_name]:
                    html_head = dict_widgets[widget_name]['widget_dashboard_head']
                else:
                    html_head = ""
                fw.write(html_head)
                fw.close()
            set_user_grp(path_head, 'mycodo', 'mycodo')

            filename_title_bar = "widget_template_{}_title_bar.html".format(widget_name)
            path_title_bar = os.path.join(PATH_HTML_USER, filename_title_bar)
            with open(path_title_bar, 'w') as fw:
                if 'widget_dashboard_title_bar' in dict_widgets[widget_name]:
                    html_title_bar = dict_widgets[widget_name]['widget_dashboard_title_bar']
                else:
                    html_title_bar = ""
                fw.write(html_title_bar)
                fw.close()
            set_user_grp(path_title_bar, 'mycodo', 'mycodo')

            filename_body = "widget_template_{}_body.html".format(widget_name)
            path_body = os.path.join(PATH_HTML_USER, filename_body)
            with open(path_body, 'w') as fw:
                if 'widget_dashboard_body' in dict_widgets[widget_name]:
                    html_body = dict_widgets[widget_name]['widget_dashboard_body']
                else:
                    html_body = ""
                fw.write(html_body)
                fw.close()
            set_user_grp(path_body, 'mycodo', 'mycodo')

            filename_configure_options = "widget_template_{}_configure_options.html".format(widget_name)
            path_configure_options = os.path.join(PATH_HTML_USER, filename_configure_options)
            with open(path_configure_options, 'w') as fw:
                if 'widget_dashboard_configure_options' in dict_widgets[widget_name]:
                    html_configure_options = dict_widgets[widget_name]['widget_dashboard_configure_options']
                else:
                    html_configure_options = ""
                fw.write(html_configure_options)
                fw.close()
            set_user_grp(path_configure_options, 'mycodo', 'mycodo')

            filename_js = "widget_template_{}_js.html".format(widget_name)
            path_js = os.path.join(PATH_HTML_USER, filename_js)
            with open(path_js, 'w') as fw:
                if 'widget_dashboard_js' in dict_widgets[widget_name]:
                    html_js = dict_widgets[widget_name]['widget_dashboard_js']
                else:
                    html_js = ""
                fw.write(html_js)
                fw.close()
            set_user_grp(path_js, 'mycodo', 'mycodo')

            filename_js_ready = "widget_template_{}_js_ready.html".format(widget_name)
            path_js_ready = os.path.join(PATH_HTML_USER, filename_js_ready)
            with open(path_js_ready, 'w') as fw:
                if 'widget_dashboard_js_ready' in dict_widgets[widget_name]:
                    html_js_ready = dict_widgets[widget_name]['widget_dashboard_js_ready']
                else:
                    html_js_ready = ""
                fw.write(html_js_ready)
                fw.close()
            set_user_grp(path_js_ready, 'mycodo', 'mycodo')

            filename_js_ready_end = "widget_template_{}_js_ready_end.html".format(widget_name)
            path_js_ready_end = os.path.join(PATH_HTML_USER, filename_js_ready_end)
            with open(path_js_ready_end, 'w') as fw:
                if 'widget_dashboard_js_ready_end' in dict_widgets[widget_name]:
                    html_js_ready_end = dict_widgets[widget_name]['widget_dashboard_js_ready_end']
                else:
                    html_js_ready_end = ""
                fw.write(html_js_ready_end)
                fw.close()
            set_user_grp(path_js_ready_end, 'mycodo', 'mycodo')
        except Exception:
            logger.exception("Generating widget HTML for widget: {}".format(widget_name))


def parse_widget_information(exclude_custom=False):
    """Parses the variables assigned in each Widget and return a dictionary of IDs and values"""
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

            full_path = "{}/{}".format(real_path, each_file)
            widget_custom = load_module_from_file(full_path, 'widgets')

            if not hasattr(widget_custom, 'WIDGET_INFORMATION'):
                continue

            # Populate dictionary of widget information
            if widget_custom.WIDGET_INFORMATION['widget_name_unique'] in dict_widgets:
                logger.error("Error: Cannot add widget modules because it does not have a unique name: {name}".format(
                    name=widget_custom.WIDGET_INFORMATION['widget_name_unique']))
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

            # Which form options to display and whether each option is enabled
            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'options_enabled')
            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'options_disabled')

            # Misc
            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'period')

            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'execute_at_creation')
            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'execute_at_modification')
            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'execute_at_deletion')
            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'generate_page_variables')

            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'custom_options_message')
            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'custom_options')

            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'custom_actions_message')
            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'custom_actions')

            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'widget_dashboard_head')
            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'widget_dashboard_title_bar')
            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'widget_dashboard_body')
            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'widget_dashboard_configure_options')
            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'widget_dashboard_js')
            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'widget_dashboard_js_ready')
            dict_widgets = dict_has_value(dict_widgets, widget_custom, 'widget_dashboard_js_ready_end')

    return dict_widgets
