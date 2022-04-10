# coding=utf-8
#
#  custom_widget_example_endpoints.py - Simple example dashboard widget that creates 2 new endpoints
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
#
import logging

from flask_login import current_user

from mycodo.databases.models import Role
from mycodo.databases.models import User
from mycodo.mycodo_flask.utils.utils_general import user_has_permission
from mycodo.utils.constraints_pass import constraints_pass_positive_value

logger = logging.getLogger(__name__)


def test_user():
    """
    This endpoint will display different messages for logged in and logged out users.
    Be very careful when creating endpoints so unauthorized users don't have access
    to endpoints with sensitive information.
    """
    if not current_user.is_authenticated:
        return "You are not logged in and cannot access this endpoint"

    user = User.query.filter(User.name == current_user.name).first()
    role = Role.query.filter(Role.id == user.role_id).first()
    return_message = "You are logged in as '{}' with the role '{}' and can access this endpoint".format(
        user.name, role.name)
    if user_has_permission('edit_settings'):
        return_message += "<br/>This user has permission to Edit Settings"
    if user_has_permission('edit_controllers'):
        return_message += "<br/>This user has permission to Edit Controllers"
    if user_has_permission('edit_users'):
        return_message += "<br/>This user has permission to Edit Users"
    if user_has_permission('view_settings'):
        return_message += "<br/>This user has permission to View Settings"
    if user_has_permission('view_camera'):
        return_message += "<br/>This user has permission to View Cameras"
    if user_has_permission('view_stats'):
        return_message += "<br/>This user has permission to View Stats"
    if user_has_permission('view_logs'):
        return_message += "<br/>This user has permission to View Logs"
    if user_has_permission('reset_password'):
        return_message += "<br/>This user has permission to Reset Passwords"
    return return_message


def test_parameter(some_text):
    """
    This endpoint will accept a parameter
    """
    if not current_user.is_authenticated:
        return "You are not logged in and cannot access this endpoint"

    return_message = f"User passed some text: {some_text}"

    return return_message


WIDGET_INFORMATION = {
    'widget_name_unique': 'widget_example_endpoints',
    'widget_name': 'Example Widget (Endpoints)',
    'widget_library': '',
    'no_class': True,

    'url_manufacturer': 'https://www.hackaday.com',
    'url_datasheet': 'https://www.digikey.com',
    'url_product_purchase': [
        'https://www.digikey.com',
        'https://www.adafruit.com'
    ],
    'url_additional': 'https://github.com',

    'endpoints': [
        # Route URL, route endpoint name, view function, methods
        ("/test_user", "test_user", test_user, ["GET"]),
        ("/test_parameter/<some_text>", "test_parameter", test_parameter, ["GET"])
    ],

    'message': 'This widget is an example endpoint widget, which will create the new endpoint '
               'at /test_user and /test_parameter/<some_text>. Open <a href="/test_user">This Link</a> '
               'and <a href="/test_parameter/thisissometext">This Link</a> to see this new endpoints.',

    # Any dependencies required by the output module. An empty list means no dependencies are required.
    'dependencies_module': [],

    # A message to be displayed on the dependency install page
    'dependencies_message': 'Are you sure you want to install these dependencies? They require...',

    'widget_width': 8,
    'widget_height': 8,

    'custom_options': [
        {
            'id': 'font_em_body',
            'type': 'float',
            'default_value': 1.5,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Body Font Size (em)',
            'phrase': 'The font size of the body text'
        },
        {
            'id': 'body_text',
            'type': 'text',
            'default_value': """Open this Widget's configuration menu and read its description. Click <a href="/test_user">here</a> and <a href="/test_parameter/thisissometext">here</a> to view the newly-created endpoints.""",
            'name': 'Body Text',
            'phrase': 'The body text of the widget'
        },
    ],

    'widget_dashboard_head': """<!-- No head content -->""",
    'widget_dashboard_title_bar': """<span style="padding-right: 0.5em; font-size: {{each_widget.font_em_name}}em">{{each_widget.name}}</span>""",
    'widget_dashboard_body': """<span style="font-size: {{widget_options['font_em_body']}}em">{{widget_options['body_text']|safe}}</span>""",
    'widget_dashboard_js': """<!-- No JS content -->""",
    'widget_dashboard_js_ready': """<!-- No JS ready content -->""",
    'widget_dashboard_js_ready_end': """<!-- No JS ready end content -->"""
}
