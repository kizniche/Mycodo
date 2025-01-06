# -*- coding: utf-8 -*-
import logging
import os
import re
import stat
import subprocess
import threading
import time
import traceback
from tempfile import NamedTemporaryFile

import bcrypt
import flask_login
import sqlalchemy
from flask import flash
from flask import redirect
from flask import url_for
from flask_babel import gettext
from sqlalchemy import and_
from sqlalchemy import or_

from mycodo.config import DAEMON_LOG_FILE
from mycodo.config import DEPENDENCY_INIT_FILE
from mycodo.config import DEPENDENCY_LOG_FILE
from mycodo.config import INSTALL_DIRECTORY
from mycodo.config import PATH_ACTIONS_CUSTOM
from mycodo.config import PATH_FUNCTIONS_CUSTOM
from mycodo.config import PATH_INPUTS_CUSTOM
from mycodo.config import PATH_OUTPUTS_CUSTOM
from mycodo.config import PATH_TEMPLATE_USER
from mycodo.config import PATH_WIDGETS_CUSTOM
from mycodo.config import UPGRADE_INIT_FILE
from mycodo.config_devices_units import MEASUREMENTS
from mycodo.config_devices_units import UNITS
from mycodo.config_translations import TRANSLATIONS
from mycodo.databases import set_api_key
from mycodo.databases.models import Actions
from mycodo.databases.models import Conversion
from mycodo.databases.models import CustomController
from mycodo.databases.models import Dashboard
from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import DisplayOrder
from mycodo.databases.models import Input
from mycodo.databases.models import Measurement
from mycodo.databases.models import Misc
from mycodo.databases.models import NoteTags
from mycodo.databases.models import Notes
from mycodo.databases.models import Output
from mycodo.databases.models import OutputChannel
from mycodo.databases.models import PID
from mycodo.databases.models import Role
from mycodo.databases.models import SMTP
from mycodo.databases.models import Unit
from mycodo.databases.models import User
from mycodo.databases.models import Widget
from mycodo.mycodo_client import DaemonControl
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.utils import utils_general
from mycodo.mycodo_flask.utils.utils_general import choices_measurements
from mycodo.mycodo_flask.utils.utils_general import choices_units
from mycodo.mycodo_flask.utils.utils_general import controller_activate_deactivate
from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.mycodo_flask.utils.utils_general import flash_form_errors
from mycodo.mycodo_flask.utils.utils_general import flash_success_errors
from mycodo.utils.actions import parse_action_information
from mycodo.utils.database import db_retrieve_table
from mycodo.utils.functions import parse_function_information
from mycodo.utils.inputs import parse_input_information
from mycodo.utils.layouts import update_layout
from mycodo.utils.modules import load_module_from_file
from mycodo.utils.outputs import parse_output_information
from mycodo.utils.send_data import send_email
from mycodo.utils.system_pi import all_conversions
from mycodo.utils.system_pi import assure_path_exists
from mycodo.utils.system_pi import base64_encode_bytes
from mycodo.utils.system_pi import cmd_output
from mycodo.utils.system_pi import set_user_grp
from mycodo.utils.utils import test_password
from mycodo.utils.utils import test_username
from mycodo.utils.widget_generate_html import generate_widget_html
from mycodo.utils.widgets import parse_widget_information

logger = logging.getLogger(__name__)

#
# User manipulation
#

def user_roles(form):
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }
    page_refresh = False

    if not messages["error"]:
        if form.user_role_add.data:
            new_role = Role()
            new_role.name = form.name.data
            new_role.view_logs = form.view_logs.data
            new_role.view_camera = form.view_camera.data
            new_role.view_stats = form.view_stats.data
            new_role.view_settings = form.view_settings.data
            new_role.edit_users = form.edit_users.data
            new_role.edit_settings = form.edit_settings.data
            new_role.edit_controllers = form.edit_controllers.data
            new_role.reset_password = form.reset_password.data
            try:
                new_role.save()
                page_refresh = True
                messages["success"].append('{action} {controller}'.format(
                    action=TRANSLATIONS['add']['title'],
                    controller=gettext("User Role")))
            except sqlalchemy.exc.OperationalError as except_msg:
                messages["error"].append(except_msg)
            except sqlalchemy.exc.IntegrityError as except_msg:
                messages["error"].append(except_msg)
        elif form.user_role_save.data:
            mod_role = Role.query.filter(
                Role.unique_id == form.role_id.data).first()
            mod_role.view_logs = form.view_logs.data
            mod_role.view_camera = form.view_camera.data
            mod_role.view_stats = form.view_stats.data
            mod_role.view_settings = form.view_settings.data
            mod_role.edit_users = form.edit_users.data
            mod_role.edit_settings = form.edit_settings.data
            mod_role.edit_controllers = form.edit_controllers.data
            mod_role.reset_password = form.reset_password.data
            db.session.commit()
            messages["success"].append('{action} {controller}'.format(
                action=TRANSLATIONS['modify']['title'],
                controller=gettext("User Role")))
        elif form.user_role_delete.data:
            user = User().query.filter(User.role_id == form.role_id.data)
            role = Role().query.filter(Role.unique_id == form.role_id.data).first()
            if role.id == 1:
                messages["error"].append("Cannot delete role: Admin role is protected")
            if user.count():
                messages["error"].append(
                    "Cannot delete role if it is assigned to a user. "
                    "Change the user to another role and try again.")
            else:
                delete_entry_with_id(Role, form.role_id.data)
                messages["success"].append('{action} {controller}'.format(
                    action=TRANSLATIONS['delete']['title'],
                    controller=gettext("User Role")))

    return messages, page_refresh


def user(form):
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }

    misc = Misc.query.first()
    misc.default_login_page = form.default_login_page.data

    if not messages["error"]:
        try:
            db.session.commit()
            messages["success"].append('{action} {controller}'.format(
                action=TRANSLATIONS['save']['title'],
                controller=TRANSLATIONS['user']['title']))
        except sqlalchemy.exc.OperationalError as except_msg:
            messages["error"].append(except_msg)
        except sqlalchemy.exc.IntegrityError as except_msg:
            messages["error"].append(except_msg)

    return messages


def user_add(form):
    action = '{action} {controller} {user}'.format(
        action=TRANSLATIONS['add']['title'],
        controller=TRANSLATIONS['user']['title'],
        user=form.user_name.data.lower())
    error = []

    if form.validate():
        new_user = User()
        new_user.name = form.user_name.data.lower()
        if not test_username(new_user.name):
            error.append(gettext(
                "Invalid user name. Must be between 2 and 64 characters "
                "and only contain letters and numbers."))

        new_user.email = form.email.data
        if User.query.filter_by(email=new_user.email).count():
            error.append(gettext(
                "Another user already has that email address."))

        if not test_password(form.password_new.data):
            error.append(gettext(
                "Invalid password. Must be between 6 and 64 characters "
                "and only contain letters, numbers, and symbols."))

        if form.password_new.data != form.password_repeat.data:
            error.append(gettext("Passwords do not match. Please try again."))

        if form.code.data:
            try:
                code_int = int(form.code.data)
                if len(str(code_int)) < 4:
                    error.append("Keypad code must be a numerical value of 4 or more digits")
                new_user.code = code_int
            except:
                error.append("Keypad code must be a numerical value of 4 or more digits")

        if not error:
            new_user.set_password(form.password_new.data)
            role = Role.query.filter(
                Role.name == form.addRole.data).first()
            new_user.role_id = role.id
            new_user.theme = form.theme.data
            try:
                new_user.save()
            except sqlalchemy.exc.OperationalError as except_msg:
                error.append(except_msg)
            except sqlalchemy.exc.IntegrityError as except_msg:
                error.append(except_msg)

        flash_success_errors(
            error, action, url_for('routes_settings.settings_users'))
    else:
        flash_form_errors(form)


def generate_api_key(form):
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }
    api_key = None

    try:
        mod_user = User.query.filter(
            User.unique_id == form.user_id.data).first()
        api_key = set_api_key(128)
        mod_user.api_key = api_key
        db.session.commit()
        messages["success"].append("Generated API Key")
    except Exception as except_msg:
        messages["error"].append(except_msg)

    return messages, base64_encode_bytes(api_key)


def change_preferences(form):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['modify']['title'],
        controller=TRANSLATIONS['theme']['title'])
    error = []

    try:
        mod_user = User.query.filter(
            User.id == flask_login.current_user.id).first()
        mod_user.theme = form.theme.data
        mod_user.language = form.language.data
        db.session.commit()
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(
        error, action, url_for('routes_settings.settings_users'))


def user_mod(form):
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }
    logout = False

    try:
        mod_user = User.query.filter(
            User.unique_id == form.user_id.data).first()
        mod_user.email = form.email.data

        if form.code.data == "0":
            mod_user.code = None
        elif form.code.data:
            try:
                code_int = int(form.code.data)
                if len(str(code_int)) < 4:
                    messages["error"].append("Keypad code must be a numerical value of 4 or more digits")
                mod_user.code = code_int
            except:
                messages["error"].append("Keypad code must be a numerical value of 4 or more digits")

        # Only change the password if it's entered in the form
        if form.password_new.data != '':
            if not utils_general.user_has_permission('reset_password'):
                messages["error"].append("Cannot change user password")
            if not test_password(form.password_new.data):
                messages["error"].append(gettext("Invalid password"))
            if form.password_new.data != form.password_repeat.data:
                messages["error"].append(gettext(
                    "Passwords do not match. Please try again."))
            mod_user.password_hash = bcrypt.hashpw(
                form.password_new.data.encode('utf-8'),
                bcrypt.gensalt())
            if flask_login.current_user.id == form.user_id.data:
                logout = True

        current_user_name = User.query.filter(
            User.unique_id == form.user_id.data).first().name
        if (mod_user.role_id == 1 and
                mod_user.role_id != form.role_id.data and
                flask_login.current_user.name == current_user_name):
            messages["error"].append(
                "Cannot change currently-logged in user's role from Admin")

        if not messages["error"]:
            mod_user.role_id = form.role_id.data
            mod_user.theme = form.theme.data
            db.session.commit()
            messages["success"].append('{action} {controller} {user}'.format(
                action=TRANSLATIONS['modify']['title'],
                controller=TRANSLATIONS['user']['title'],
                user=mod_user.name))
    except Exception as except_msg:
        messages["error"].append(except_msg)

    return messages, logout


def user_del(form):
    """Delete user from SQL database"""
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }

    if form.user_id.data == flask_login.current_user.id:
        messages["error"].append("Cannot delete the currently-logged in user")

    if not messages["error"]:
        try:
            user = User.query.filter(
                User.unique_id == form.user_id.data).first()
            user.delete()
            messages["success"].append('{action} {controller} {user}'.format(
                action=TRANSLATIONS['delete']['title'],
                controller=TRANSLATIONS['user']['title'],
                user=user.name))
        except Exception as except_msg:
            messages["error"].append(except_msg)

    return messages


#
# Settings modifications
#


def settings_general_mod(form):
    """Modify General settings."""
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }

    if form.validate():
        if (form.output_usage_report_span.data == 'monthly' and
                not 0 < form.output_usage_report_day.data < 29):
            messages["error"].append("Day Options: Daily: 1-7 (1=Monday), Monthly: 1-28")
        elif (form.output_usage_report_span.data == 'weekly' and
                not 0 < form.output_usage_report_day.data < 8):
            messages["error"].append("Day Options: Daily: 1-7 (1=Monday), Monthly: 1-28")

        if not messages["error"]:
            try:
                reload_frontend = False
                mod_misc = Misc.query.first()

                if mod_misc.force_https != form.force_https.data:
                    mod_misc.force_https = form.force_https.data
                    reload_frontend = True

                mod_misc.rpyc_timeout = form.rpyc_timeout.data
                mod_misc.custom_css = form.custom_css.data

                if mod_misc.custom_layout != form.custom_layout.data:
                    mod_misc.custom_layout = form.custom_layout.data
                    assure_path_exists(PATH_TEMPLATE_USER)
                    update_layout(mod_misc.custom_layout)
                    reload_frontend = True

                mod_misc.brand_display = form.brand_display.data
                mod_misc.title_display = form.title_display.data
                mod_misc.hostname_override = form.hostname_override.data
                if form.brand_image.data:
                    mod_misc.brand_image = form.brand_image.data.read()
                mod_misc.brand_image_height = form.brand_image_height.data
                mod_misc.favicon_display = form.favicon_display.data
                if form.brand_favicon.data:
                    mod_misc.brand_favicon = form.brand_favicon.data.read()
                mod_misc.daemon_debug_mode = form.daemon_debug_mode.data
                mod_misc.hide_alert_success = form.hide_success.data
                mod_misc.hide_alert_info = form.hide_info.data
                mod_misc.hide_alert_warning = form.hide_warning.data
                mod_misc.hide_tooltips = form.hide_tooltips.data

                mod_misc.sample_rate_controller_conditional = form.sample_rate_controller_conditional.data
                mod_misc.sample_rate_controller_function = form.sample_rate_controller_function.data
                mod_misc.sample_rate_controller_input = form.sample_rate_controller_input.data
                mod_misc.sample_rate_controller_output = form.sample_rate_controller_output.data
                mod_misc.sample_rate_controller_pid = form.sample_rate_controller_pid.data
                mod_misc.sample_rate_controller_widget = form.sample_rate_controller_widget.data

                if form.use_database.data == "influxdb_1":
                    mod_misc.measurement_db_name = "influxdb"
                    mod_misc.measurement_db_version = "1"
                elif form.use_database.data == "influxdb_2":
                    mod_misc.measurement_db_name = "influxdb"
                    mod_misc.measurement_db_version = "2"

                mod_misc.measurement_db_retention_policy = form.measurement_db_retention_policy.data
                mod_misc.measurement_db_host = form.measurement_db_host.data
                mod_misc.measurement_db_port = form.measurement_db_port.data
                mod_misc.measurement_db_dbname = form.measurement_db_dbname.data
                mod_misc.measurement_db_user = form.measurement_db_user.data
                if (form.measurement_db_password.data and
                        form.measurement_db_password.data != mod_misc.measurement_db_password):
                    mod_misc.measurement_db_password = form.measurement_db_password.data

                mod_misc.grid_cell_height = form.grid_cell_height.data
                mod_misc.max_amps = form.max_amps.data
                mod_misc.output_usage_volts = form.output_stats_volts.data
                mod_misc.output_usage_cost = form.output_stats_cost.data
                mod_misc.output_usage_currency = form.output_stats_currency.data
                mod_misc.output_usage_dayofmonth = form.output_stats_day_month.data
                mod_misc.output_usage_report_gen = form.output_usage_report_gen.data
                mod_misc.output_usage_report_span = form.output_usage_report_span.data
                mod_misc.output_usage_report_day = form.output_usage_report_day.data
                mod_misc.output_usage_report_hour = form.output_usage_report_hour.data
                mod_misc.stats_opt_out = form.stats_opt_out.data
                mod_misc.enable_upgrade_check = form.enable_upgrade_check.data
                mod_misc.net_test_ip = form.net_test_ip.data
                mod_misc.net_test_port = form.net_test_port.data
                mod_misc.net_test_timeout = form.net_test_timeout.data

                mod_user = User.query.filter(
                    User.id == flask_login.current_user.id).first()
                mod_user.landing_page = form.landing_page.data
                mod_user.index_page = form.index_page.data
                mod_user.language = form.language.data

                db.session.commit()
                control = DaemonControl()
                control.refresh_daemon_misc_settings()
                messages["success"].append('{action} {controller}'.format(
                    action=TRANSLATIONS['modify']['title'],
                    controller=gettext("General Settings")))

                if reload_frontend:
                    # Reload web server
                    logger.info("Reloading frontend in 10 seconds")
                    cmd = f"sleep 10 && {INSTALL_DIRECTORY}/mycodo/scripts/mycodo_wrapper frontend_reload 2>&1"
                    subprocess.Popen(cmd, shell=True)

            except Exception as except_msg:
                messages["error"].append(except_msg)
    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages["error"].append(
                    gettext("Error in the %(field)s field - %(err)s",
                        field=getattr(form, field).label.text,
                        err=error))

    return messages


def settings_function_import(form):
    """
    Receive a function module file, check it for errors, add it to Mycodo controller list
    """
    action = '{action} {controller}'.format(
        action=gettext("Import"),
        controller=TRANSLATIONS['controller']['title'])
    error = []

    controller_info = None

    try:
        install_dir = os.path.abspath(INSTALL_DIRECTORY)
        tmp_directory = os.path.join(install_dir, 'mycodo/functions/tmp_functions')
        assure_path_exists(tmp_directory)
        assure_path_exists(PATH_FUNCTIONS_CUSTOM)
        tmp_name = 'tmp_function_testing.py'
        full_path_tmp = os.path.join(tmp_directory, tmp_name)

        if not form.import_controller_file.data:
            error.append('No file present')
        elif form.import_controller_file.data.filename == '':
            error.append('No file name')
        else:
            form.import_controller_file.data.save(full_path_tmp)

        try:
            controller_info, status = load_module_from_file(full_path_tmp, 'functions')
            if not controller_info or not hasattr(controller_info, 'FUNCTION_INFORMATION'):
                error.append("Could not load FUNCTION_INFORMATION dictionary from "
                             "the uploaded controller module")
        except Exception:
            error.append("Could not load uploaded file as a python module:\n"
                         "{}".format(traceback.format_exc()))

        dict_controllers = parse_function_information()
        list_controllers = []
        for each_key in dict_controllers.keys():
            list_controllers.append(each_key.lower())

        if not error:
            if 'function_name_unique' not in controller_info.FUNCTION_INFORMATION:
                error.append(
                    "'function_name_unique' not found in "
                    "FUNCTION_INFORMATION dictionary")
            elif controller_info.FUNCTION_INFORMATION['function_name_unique'] == '':
                error.append("'function_name_unique' is empty")
            elif controller_info.FUNCTION_INFORMATION['function_name_unique'].lower() in list_controllers:
                error.append(
                    "'function_name_unique' is not unique, there "
                    "is already an controller with that name ({})".format(
                        controller_info.FUNCTION_INFORMATION['function_name_unique'].lower()))

            if 'function_name' not in controller_info.FUNCTION_INFORMATION:
                error.append("'function_name' not found in FUNCTION_INFORMATION dictionary")
            elif controller_info.FUNCTION_INFORMATION['function_name'] == '':
                error.append("'function_name' is empty")

            if 'dependencies_module' in controller_info.FUNCTION_INFORMATION:
                if not isinstance(controller_info.FUNCTION_INFORMATION['dependencies_module'], list):
                    error.append("'dependencies_module' must be a list of tuples")
                else:
                    for each_dep in controller_info.FUNCTION_INFORMATION['dependencies_module']:
                        if not isinstance(each_dep, tuple):
                            error.append("'dependencies_module' must be a list of tuples")
                        elif len(each_dep) != 3:
                            error.append("'dependencies_module': tuples in list must have 3 items")
                        elif not each_dep[0] or not each_dep[1] or not each_dep[2]:
                            error.append(
                                "'dependencies_module': tuples in list must "
                                "not be empty")
                        elif each_dep[0] not in ['internal', 'pip-pypi', 'apt']:
                            error.append(
                                "'dependencies_module': first in tuple "
                                "must be 'internal', 'pip-pypi', "
                                "or 'apt'")

        if not error:
            # Determine filename
            unique_name = '{}.py'.format(controller_info.FUNCTION_INFORMATION['function_name_unique'].lower())

            # Move module from temp directory to function directory
            full_path_final = os.path.join(PATH_FUNCTIONS_CUSTOM, unique_name)
            os.rename(full_path_tmp, full_path_final)

            # Reload frontend to refresh the controllers
            cmd = '{path}/mycodo/scripts/mycodo_wrapper frontend_reload 2>&1'.format(
                path=install_dir)
            subprocess.Popen(cmd, shell=True)
            flash('Frontend reloaded to scan for new Controller Modules', 'success')

    except Exception as err:
        logger.exception("Function Import")
        error.append("Exception: {}".format(err))

    flash_success_errors(error, action, url_for('routes_settings.settings_function'))


def settings_function_delete(form):
    action = '{action} {controller}'.format(
        action=gettext("Import"),
        controller=TRANSLATIONS['controller']['title'])
    error = []

    controller_device_name = form.controller_id.data
    file_name = '{}.py'.format(form.controller_id.data.lower())
    full_path_file = os.path.join(PATH_FUNCTIONS_CUSTOM, file_name)

    if not error:
        # Check if any Controller entries exist
        controller_dev = CustomController.query.filter(
            CustomController.device == controller_device_name).count()
        if controller_dev:
            error.append("Cannot delete Controller Module if there are still "
                         "Controller entries using it. Deactivate and delete all "
                         "Controller entries that use this module before deleting "
                         "the module.")

    if not error:
        os.remove(full_path_file)

        # Reload frontend to refresh the controllers
        cmd = '{path}/mycodo/scripts/mycodo_wrapper frontend_reload 2>&1'.format(
            path=os.path.abspath(INSTALL_DIRECTORY))
        subprocess.Popen(cmd, shell=True)
        flash('Frontend reloaded to scan for new Controller Modules', 'success')

    flash_success_errors(error, action, url_for('routes_settings.settings_function'))


def settings_action_import(form):
    """
    Receive an action module file, check it for errors, add it to Mycodo controller list
    """
    action = '{action} {controller}'.format(
        action=gettext("Import"),
        controller=TRANSLATIONS['actions']['title'])
    error = []

    action_info = None

    try:
        install_dir = os.path.abspath(INSTALL_DIRECTORY)
        tmp_directory = os.path.join(install_dir, 'mycodo/actions/tmp_actions')
        assure_path_exists(tmp_directory)
        assure_path_exists(PATH_ACTIONS_CUSTOM)
        tmp_name = 'tmp_action_testing.py'
        full_path_tmp = os.path.join(tmp_directory, tmp_name)

        if not form.import_action_file.data:
            error.append('No file present')
        elif form.import_action_file.data.filename == '':
            error.append('No file name')
        else:
            form.import_action_file.data.save(full_path_tmp)

        try:
            action_info, status = load_module_from_file(full_path_tmp, 'actions')
            if not action_info or not hasattr(action_info, 'ACTION_INFORMATION'):
                error.append("Could not load ACTION_INFORMATION dictionary from "
                             "the uploaded action module")
        except Exception:
            error.append("Could not load uploaded file as a python module:\n"
                         "{}".format(traceback.format_exc()))

        dict_actions = parse_action_information()
        list_actions = []
        for each_key in dict_actions.keys():
            list_actions.append(each_key.lower())

        if not error:
            if 'name_unique' not in action_info.ACTION_INFORMATION:
                error.append(
                    "'name_unique' not found in "
                    "ACTION_INFORMATION dictionary")
            elif action_info.ACTION_INFORMATION['name_unique'] == '':
                error.append("'name_unique' is empty")
            elif action_info.ACTION_INFORMATION['name_unique'].lower() in list_actions:
                error.append(
                    "'name_unique' is not unique, there "
                    "is already an action with that name ({})".format(
                        action_info.ACTION_INFORMATION['name_unique'].lower()))

            if 'name' not in action_info.ACTION_INFORMATION:
                error.append("'name' not found in ACTION_INFORMATION dictionary")
            elif action_info.ACTION_INFORMATION['name'] == '':
                error.append("'name' is empty")

            if 'dependencies_module' in action_info.ACTION_INFORMATION:
                if not isinstance(action_info.ACTION_INFORMATION['dependencies_module'], list):
                    error.append("'dependencies_module' must be a list of tuples")
                else:
                    for each_dep in action_info.ACTION_INFORMATION['dependencies_module']:
                        if not isinstance(each_dep, tuple):
                            error.append("'dependencies_module' must be a list of tuples")
                        elif len(each_dep) != 3:
                            error.append("'dependencies_module': tuples in list must have 3 items")
                        elif not each_dep[0] or not each_dep[1] or not each_dep[2]:
                            error.append(
                                "'dependencies_module': tuples in list must "
                                "not be empty")
                        elif each_dep[0] not in ['internal', 'pip-pypi', 'apt']:
                            error.append(
                                "'dependencies_module': first in tuple "
                                "must be 'internal', 'pip-pypi', "
                                "or 'apt'")

        if not error:
            # Determine filename
            unique_name = '{}.py'.format(action_info.ACTION_INFORMATION['name_unique'].lower())

            # Move module from temp directory to function directory
            full_path_final = os.path.join(PATH_ACTIONS_CUSTOM, unique_name)
            os.rename(full_path_tmp, full_path_final)

            # Reload frontend to refresh the actions
            cmd = '{path}/mycodo/scripts/mycodo_wrapper frontend_reload 2>&1'.format(
                path=install_dir)
            subprocess.Popen(cmd, shell=True)
            flash('Frontend reloaded to scan for new Action Modules', 'success')

    except Exception as err:
        logger.exception("Action Import")
        error.append("Exception: {}".format(err))

    flash_success_errors(error, action, url_for('routes_settings.settings_action'))


def settings_action_delete(form):
    action = '{action} {controller}'.format(
        action=gettext("Import"),
        controller=TRANSLATIONS['actions']['title'])
    error = []

    action_device_name = form.action_id.data
    file_name = '{}.py'.format(form.action_id.data.lower())
    full_path_file = os.path.join(PATH_ACTIONS_CUSTOM, file_name)

    # Check if any action entries exist
    action_dev = Actions.query.filter(
        Actions.action_type == action_device_name).count()
    if action_dev:
        error.append("Cannot delete Action Module if there are still "
                     "Action entries using it. Delete all "
                     "Action entries that use this module before deleting "
                     "the module.")

    if not error:
        os.remove(full_path_file)

        # Reload frontend to refresh the actions
        cmd = '{path}/mycodo/scripts/mycodo_wrapper frontend_reload 2>&1'.format(
            path=os.path.abspath(INSTALL_DIRECTORY))
        subprocess.Popen(cmd, shell=True)
        flash('Frontend reloaded to scan for new Action Modules', 'success')

    flash_success_errors(error, action, url_for('routes_settings.settings_function'))


def settings_input_import(form):
    """
    Receive an input module file, check it for errors, add it to Mycodo input list
    """
    action = '{action} {controller}'.format(
        action=gettext("Import"),
        controller=TRANSLATIONS['input']['title'])
    error = []

    input_info = None

    try:
        # correct_format = 'Mycodo_MYCODOVERSION_Settings_DBVERSION_HOST_DATETIME.zip'
        install_dir = os.path.abspath(INSTALL_DIRECTORY)
        tmp_directory = os.path.join(install_dir, 'mycodo/inputs/tmp_inputs')
        assure_path_exists(tmp_directory)
        assure_path_exists(PATH_INPUTS_CUSTOM)
        tmp_name = 'tmp_input_testing.py'
        full_path_tmp = os.path.join(tmp_directory, tmp_name)

        if not form.import_input_file.data:
            error.append('No file present')
        elif form.import_input_file.data.filename == '':
            error.append('No file name')
        else:
            form.import_input_file.data.save(full_path_tmp)

        try:
            input_info, status = load_module_from_file(full_path_tmp, 'inputs')
            if not input_info and status != "success":
                error.append(status)
            if input_info and not hasattr(input_info, 'INPUT_INFORMATION'):
                error.append("Could not load INPUT_INFORMATION dictionary from "
                             "the uploaded input module")
        except Exception:
            error.append("Could not load uploaded file as a python module:\n"
                         "{}".format(traceback.format_exc()))

        dict_inputs = parse_input_information()
        list_inputs = []
        for each_key in dict_inputs.keys():
            list_inputs.append(each_key.lower())

        if not error:
            if 'input_name_unique' not in input_info.INPUT_INFORMATION:
                error.append(
                    "'input_name_unique' not found in "
                    "INPUT_INFORMATION dictionary")
            elif input_info.INPUT_INFORMATION['input_name_unique'] == '':
                error.append("'input_name_unique' is empty")
            elif input_info.INPUT_INFORMATION['input_name_unique'].lower() in list_inputs:
                error.append(
                    "'input_name_unique' is not unique, there "
                    "is already an input with that name ({})".format(
                        input_info.INPUT_INFORMATION['input_name_unique'].lower()))

            if 'input_manufacturer' not in input_info.INPUT_INFORMATION:
                error.append(
                    "'input_manufacturer' not found in "
                    "INPUT_INFORMATION dictionary")
            elif input_info.INPUT_INFORMATION['input_manufacturer'] == '':
                error.append("'input_manufacturer' is empty")

            if 'input_name' not in input_info.INPUT_INFORMATION:
                error.append("'input_name' not found in INPUT_INFORMATION dictionary")
            elif input_info.INPUT_INFORMATION['input_name'] == '':
                error.append("'input_name' is empty")

            if 'measurements_name' not in input_info.INPUT_INFORMATION:
                error.append(
                    "'measurements_name' not found in "
                    "INPUT_INFORMATION dictionary")
            elif input_info.INPUT_INFORMATION['measurements_name'] == '':
                error.append("'measurements_name' list is empty")

            if 'measurements_dict' not in input_info.INPUT_INFORMATION:
                error.append(
                    "'measurements_dict' not found in "
                    "INPUT_INFORMATION dictionary")
            elif not input_info.INPUT_INFORMATION['measurements_dict']:
                if ('measurements_variable_amount' in input_info.INPUT_INFORMATION and
                   input_info.INPUT_INFORMATION['measurements_variable_amount']):
                    pass
                else:
                    error.append("'measurements_dict' list is empty")
            else:
                # Check that units and measurements exist in database
                for _, each_unit_measure in input_info.INPUT_INFORMATION['measurements_dict'].items():
                    if (each_unit_measure['unit'] not in UNITS and
                            not Unit.query.filter(Unit.name_safe == each_unit_measure['unit']).count()):
                        error.append(
                            "Unit not found in database. "
                            "Add the unit '{}' to the database before importing.".format(
                                each_unit_measure['unit']))
                    if (each_unit_measure['measurement'] not in MEASUREMENTS and
                            not Measurement.query.filter(Measurement.name_safe == each_unit_measure['measurement']).count()):
                        error.append(
                            "Measurement not found in database. "
                            "Add the measurement '{}' to the database before importing.".format(
                                each_unit_measure['measurement']))

            if 'dependencies_module' in input_info.INPUT_INFORMATION:
                if not isinstance(input_info.INPUT_INFORMATION['dependencies_module'], list):
                    error.append("'dependencies_module' must be a list of tuples")
                else:
                    for each_dep in input_info.INPUT_INFORMATION['dependencies_module']:
                        if not isinstance(each_dep, tuple):
                            error.append("'dependencies_module' must be a list of tuples")
                        elif len(each_dep) != 3:
                            error.append("'dependencies_module': tuples in list must have 3 items")
                        elif not each_dep[0] or not each_dep[1] or not each_dep[2]:
                            error.append("'dependencies_module': tuples in list must not be empty")
                        elif each_dep[0] not in ['internal', 'pip-pypi', 'apt']:
                            error.append(
                                "'dependencies_module': first in tuple "
                                "must be 'internal', 'pip-pypi', "
                                "or 'apt'")

        if not error:
            # Determine filename
            unique_name = '{}.py'.format(input_info.INPUT_INFORMATION['input_name_unique'].lower())

            # Move module from temp directory to custom_input directory
            full_path_final = os.path.join(PATH_INPUTS_CUSTOM, unique_name)
            os.rename(full_path_tmp, full_path_final)

            # Reload frontend to refresh the inputs
            cmd = '{path}/mycodo/scripts/mycodo_wrapper frontend_reload 2>&1'.format(
                path=install_dir)
            subprocess.Popen(cmd, shell=True)
            flash('Frontend reloaded to scan for new Input Modules', 'success')

    except Exception as err:
        error.append("Exception: {}".format(err))

    flash_success_errors(error, action, url_for('routes_settings.settings_input'))


def settings_input_delete(form):
    action = '{action} {controller}'.format(
        action=gettext("Import"),
        controller=TRANSLATIONS['input']['title'])
    error = []

    input_device_name = form.input_id.data
    file_name = '{}.py'.format(form.input_id.data.lower())
    full_path_file = os.path.join(PATH_INPUTS_CUSTOM, file_name)

    if not error:
        # Check if any Input entries exist
        input_dev = Input.query.filter(Input.device == input_device_name).count()
        if input_dev:
            error.append("Cannot delete Input Module if there are still "
                         "Input entries using it. Deactivate and delete all "
                         "Input entries that use this module before deleting "
                         "the module.")

    if not error:
        os.remove(full_path_file)

        # Reload frontend to refresh the inputs
        cmd = '{path}/mycodo/scripts/mycodo_wrapper frontend_reload 2>&1'.format(
            path=os.path.abspath(INSTALL_DIRECTORY))
        subprocess.Popen(cmd, shell=True)
        flash('Frontend reloaded to scan for new Input Modules', 'success')

    flash_success_errors(error, action, url_for('routes_settings.settings_input'))


def settings_output_import(form):
    """
    Receive an output module file, check it for errors, add it to Mycodo output list
    """
    action = '{action} {controller}'.format(
        action=gettext("Import"),
        controller=TRANSLATIONS['output']['title'])
    error = []

    output_info = None

    try:
        # correct_format = 'Mycodo_MYCODOVERSION_Settings_DBVERSION_HOST_DATETIME.zip'
        install_dir = os.path.abspath(INSTALL_DIRECTORY)
        tmp_directory = os.path.join(install_dir, 'mycodo/outputs/tmp_outputs')
        assure_path_exists(tmp_directory)
        assure_path_exists(PATH_OUTPUTS_CUSTOM)
        tmp_name = 'tmp_output_testing.py'
        full_path_tmp = os.path.join(tmp_directory, tmp_name)

        if not form.import_output_file.data:
            error.append('No file present')
        elif form.import_output_file.data.filename == '':
            error.append('No file name')
        else:
            form.import_output_file.data.save(full_path_tmp)

        try:
            output_info, status = load_module_from_file(full_path_tmp, 'outputs')
            if not output_info or not hasattr(output_info, 'OUTPUT_INFORMATION'):
                error.append("Could not load OUTPUT_INFORMATION dictionary from "
                             "the uploaded output module")
        except Exception:
            error.append("Could not load uploaded file as a python module:\n"
                         "{}".format(traceback.format_exc()))

        dict_outputs = parse_output_information()
        list_outputs = []
        for each_key in dict_outputs.keys():
            list_outputs.append(each_key.lower())

        if not error:
            if 'output_name_unique' not in output_info.OUTPUT_INFORMATION:
                error.append(
                    "'output_name_unique' not found in "
                    "OUTPUT_INFORMATION dictionary")
            elif output_info.OUTPUT_INFORMATION['output_name_unique'] == '':
                error.append("'output_name_unique' is empty")
            elif output_info.OUTPUT_INFORMATION['output_name_unique'].lower() in list_outputs:
                error.append(
                    "'output_name_unique' is not unique, there "
                    "is already an output with that name ({})".format(
                        output_info.OUTPUT_INFORMATION['output_name_unique'].lower()))

            if 'output_name' not in output_info.OUTPUT_INFORMATION:
                error.append("'output_name' not found in OUTPUT_INFORMATION dictionary")
            elif output_info.OUTPUT_INFORMATION['output_name'] == '':
                error.append("'output_name' is empty")

            if 'measurements_dict' not in output_info.OUTPUT_INFORMATION:
                error.append("'measurements_dict' not found in OUTPUT_INFORMATION dictionary")
            elif not output_info.OUTPUT_INFORMATION['measurements_dict']:
                if ('measurements_variable_amount' in output_info.OUTPUT_INFORMATION and
                   output_info.OUTPUT_INFORMATION['measurements_variable_amount']):
                    pass
                else:
                    error.append("'measurements_dict' list is empty")
            else:
                # Check that units and measurements exist in database
                for _, each_unit_measure in output_info.OUTPUT_INFORMATION['measurements_dict'].items():
                    if (each_unit_measure['unit'] not in UNITS and
                            not Unit.query.filter(Unit.name_safe == each_unit_measure['unit']).count()):
                        error.append(
                            "Unit not found in database. "
                            "Add the unit '{}' to the database before importing.".format(
                                each_unit_measure['unit']))
                    if (each_unit_measure['measurement'] not in MEASUREMENTS and
                            not Measurement.query.filter(Measurement.name_safe == each_unit_measure['measurement']).count()):
                        error.append(
                            "Measurement not found in database. "
                            "Add the measurement '{}' to the database before importing.".format(
                                each_unit_measure['measurement']))

            if 'dependencies_module' in output_info.OUTPUT_INFORMATION:
                if not isinstance(output_info.OUTPUT_INFORMATION['dependencies_module'], list):
                    error.append("'dependencies_module' must be a list of tuples")
                else:
                    for each_dep in output_info.OUTPUT_INFORMATION['dependencies_module']:
                        if not isinstance(each_dep, tuple):
                            error.append("'dependencies_module' must be a list of tuples")
                        elif len(each_dep) != 3:
                            error.append("'dependencies_module': tuples in list must have 3 items")
                        elif not each_dep[0] or not each_dep[1] or not each_dep[2]:
                            error.append("'dependencies_module': tuples in list must not be empty")
                        elif each_dep[0] not in ['internal', 'pip-pypi', 'apt']:
                            error.append(
                                "'dependencies_module': first in tuple "
                                "must be 'internal', 'pip-pypi', "
                                "or 'apt'")

        if not error:
            # Determine filename
            unique_name = '{}.py'.format(output_info.OUTPUT_INFORMATION['output_name_unique'].lower())

            # Move module from temp directory to custom_output directory
            full_path_final = os.path.join(PATH_OUTPUTS_CUSTOM, unique_name)
            os.rename(full_path_tmp, full_path_final)

            # Reload frontend to refresh the outputs
            cmd = '{path}/mycodo/scripts/mycodo_wrapper frontend_reload 2>&1'.format(
                path=install_dir)
            subprocess.Popen(cmd, shell=True)
            flash('Frontend reloaded to scan for new Output Modules', 'success')

    except Exception as err:
        error.append("Exception: {}".format(err))

    flash_success_errors(error, action, url_for('routes_settings.settings_output'))


def settings_output_delete(form):
    action = '{action} {controller}'.format(
        action=gettext("Import"),
        controller=TRANSLATIONS['output']['title'])
    error = []

    output_device_name = form.output_id.data
    file_name = '{}.py'.format(form.output_id.data.lower())
    full_path_file = os.path.join(PATH_OUTPUTS_CUSTOM, file_name)

    if not error:
        # Check if any Output entries exist
        output_dev = Output.query.filter(Output.output_type == output_device_name).count()
        if output_dev:
            error.append("Cannot delete Output Module if there are still "
                         "Output entries using it. Delete all Output entries "
                         "that use this module before deleting the module.")

    if not error:
        os.remove(full_path_file)

        # Reload frontend to refresh the outputs
        cmd = '{path}/mycodo/scripts/mycodo_wrapper frontend_reload 2>&1'.format(
            path=os.path.abspath(INSTALL_DIRECTORY))
        subprocess.Popen(cmd, shell=True)
        flash('Frontend reloaded to scan for new Output Modules', 'success')

    flash_success_errors(error, action, url_for('routes_settings.settings_output'))


def settings_widget_import(form):
    """
    Receive an widget module file, check it for errors, add it to Mycodo widget list
    """
    action = '{action} {controller}'.format(
        action=gettext("Import"),
        controller=TRANSLATIONS['widget']['title'])
    error = []

    widget_info = None

    try:
        # correct_format = 'Mycodo_MYCODOVERSION_Settings_DBVERSION_HOST_DATETIME.zip'
        install_dir = os.path.abspath(INSTALL_DIRECTORY)
        tmp_directory = os.path.join(install_dir, 'mycodo/widgets/tmp_widgets')
        assure_path_exists(tmp_directory)
        assure_path_exists(PATH_WIDGETS_CUSTOM)
        tmp_name = 'tmp_widget_testing.py'
        full_path_tmp = os.path.join(tmp_directory, tmp_name)

        if not form.import_widget_file.data:
            error.append('No file present')
        elif form.import_widget_file.data.filename == '':
            error.append('No file name')
        else:
            form.import_widget_file.data.save(full_path_tmp)

        try:
            widget_info, status = load_module_from_file(full_path_tmp, 'widgets')
            if not widget_info or not hasattr(widget_info, 'WIDGET_INFORMATION'):
                error.append("Could not load WIDGET_INFORMATION dictionary from "
                             "the uploaded widget module")
        except Exception:
            error.append("Could not load uploaded file as a python module:\n"
                         "{}".format(traceback.format_exc()))

        dict_widgets = parse_widget_information()
        list_widgets = []
        for each_key in dict_widgets.keys():
            list_widgets.append(each_key.lower())

        if not error:
            if 'widget_name_unique' not in widget_info.WIDGET_INFORMATION:
                error.append("'widget_name_unique' not found in WIDGET_INFORMATION dictionary")
            elif widget_info.WIDGET_INFORMATION['widget_name_unique'] == '':
                error.append("'widget_name_unique' is empty")
            elif widget_info.WIDGET_INFORMATION['widget_name_unique'].lower() in list_widgets:
                error.append(
                    "'widget_name_unique' is not unique, there "
                    "is already an widget with that name ({})".format(
                        widget_info.WIDGET_INFORMATION['widget_name_unique'].lower()))

            if 'widget_name' not in widget_info.WIDGET_INFORMATION:
                error.append("'widget_name' not found in WIDGET_INFORMATION dictionary")
            elif widget_info.WIDGET_INFORMATION['widget_name'] == '':
                error.append("'widget_name' is empty")

            if 'dependencies_module' in widget_info.WIDGET_INFORMATION:
                if not isinstance(widget_info.WIDGET_INFORMATION['dependencies_module'], list):
                    error.append("'dependencies_module' must be a list of tuples")
                else:
                    for each_dep in widget_info.WIDGET_INFORMATION['dependencies_module']:
                        if not isinstance(each_dep, tuple):
                            error.append("'dependencies_module' must be a list of tuples")
                        elif len(each_dep) != 3:
                            error.append("'dependencies_module': tuples in list must have 3 items")
                        elif not each_dep[0] or not each_dep[1] or not each_dep[2]:
                            error.append("'dependencies_module': tuples in list must not be empty")
                        elif each_dep[0] not in ['internal', 'pip-pypi', 'apt']:
                            error.append(
                                "'dependencies_module': first in tuple "
                                "must be 'internal', 'pip-pypi', "
                                "or 'apt'")

        if not error:
            # Determine filename
            unique_name = '{}.py'.format(widget_info.WIDGET_INFORMATION['widget_name_unique'].lower())

            # Move module from temp directory to custom_widget directory
            full_path_final = os.path.join(PATH_WIDGETS_CUSTOM, unique_name)
            os.rename(full_path_tmp, full_path_final)

            generate_widget_html()

            # Reload frontend to refresh the widgets
            cmd = '{path}/mycodo/scripts/mycodo_wrapper frontend_reload 2>&1'.format(
                path=install_dir)
            subprocess.Popen(cmd, shell=True)
            flash('Frontend reloaded to scan for new Widget Modules', 'success')

    except Exception as err:
        error.append("Exception: {}".format(err))

    flash_success_errors(error, action, url_for('routes_settings.settings_widget'))


def settings_widget_delete(form):
    action = '{action} {controller}'.format(
        action=gettext("Import"),
        controller=TRANSLATIONS['widget']['title'])
    error = []

    widget_device_name = form.widget_id.data
    file_name = '{}.py'.format(form.widget_id.data.lower())
    full_path_file = os.path.join(PATH_WIDGETS_CUSTOM, file_name)

    if not error:
        # Check if any Widget entries exist
        widget_dev = Widget.query.filter(Widget.graph_type == widget_device_name).count()
        if widget_dev:
            error.append("Cannot delete Widget Module if there are still "
                         "Widget entries using it. Delete all Widget entries "
                         "that use this module before deleting the module.")

    if not error:
        os.remove(full_path_file)

        # Reload frontend to refresh the widgets
        cmd = '{path}/mycodo/scripts/mycodo_wrapper frontend_reload 2>&1'.format(
            path=os.path.abspath(INSTALL_DIRECTORY))
        subprocess.Popen(cmd, shell=True)
        flash('Frontend reloaded to scan for new Widget Modules', 'success')

    flash_success_errors(error, action, url_for('routes_settings.settings_widget'))


def settings_measurement_add(form):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['add']['title'],
        controller=TRANSLATIONS['measurement']['title'])
    error = []
    choices_meas = choices_measurements(Measurement.query.all())

    new_measurement = Measurement()
    new_measurement.name = form.name.data
    new_measurement.units = ",".join(form.units.data)

    name_safe = re.sub('[^0-9a-zA-Z]+', '_', form.id.data)
    if name_safe.endswith('_'):
        name_safe = name_safe[:-1]
    if name_safe in choices_meas:
        error.append("Measurement name already exists: {name}".format(
            name=name_safe))

    new_measurement.name_safe = name_safe

    try:
        if not error:
            new_measurement.save()
            flash(gettext(
                "Measurement with ID %(id)s (%(uuid)s) successfully added",
                id=new_measurement.id,
                uuid=new_measurement.unique_id),
                  "success")
    except sqlalchemy.exc.OperationalError as except_msg:
        error.append(except_msg)
    except sqlalchemy.exc.IntegrityError as except_msg:
        error.append(except_msg)

    flash_success_errors(
        error, action, url_for('routes_settings.settings_measurement'))


def settings_measurement_mod(form):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['modify']['title'],
        controller=TRANSLATIONS['measurement']['title'])
    error = []
    try:
        mod_measurement = Measurement.query.filter(
            Measurement.unique_id == form.measurement_id.data).first()
        mod_measurement.name = form.name.data
        mod_measurement.units = ",".join(form.units.data)

        name_safe = re.sub('[^0-9a-zA-Z]+', '_', form.id.data)
        if name_safe.endswith('_'):
            name_safe = name_safe[:-1]

        if name_safe != mod_measurement.name_safe:  # Change measurement name
            # Ensure no Inputs depend on this measurement
            for _, each_data in parse_input_information().items():
                if 'measurements_dict' in each_data:
                    for _, each_channel_data in each_data['measurements_dict'].items():
                        if ('measurement' in each_channel_data and
                                each_channel_data['measurement'] == mod_measurement.name_safe):
                            error.append(
                                "Cannot change the name of this measurement "
                                "because an Input depends on it.")
            # Ensure a measurement doesn't already exist with the new name
            if (Measurement.query.filter(
                    and_(Measurement.name_safe == name_safe,
                         Measurement.unique_id != mod_measurement.unique_id)).count() or
                    name_safe in MEASUREMENTS):
                error.append("Measurement name already exists: {name}".format(
                    name=name_safe))
            else:
                mod_measurement.name_safe = name_safe

        if not error:
            db.session.commit()
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(
        error, action, url_for('routes_settings.settings_measurement'))


def settings_measurement_del(unique_id):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['delete']['title'],
        controller=TRANSLATIONS['measurement']['title'])
    error = []

    measurement = Measurement.query.filter(
        Measurement.unique_id == unique_id).first()

    # Ensure no Inputs depend on this measurement
    for _, each_data in parse_input_information().items():
        if 'measurements_dict' in each_data:
            for _, each_channel_data in each_data['measurements_dict'].items():
                if ('measurement' in each_channel_data and
                        each_channel_data['measurement'] == measurement.name_safe):
                    error.append("Cannot delete this measurement because "
                                 "an Input depends on it.")

    try:
        if not error:
            delete_entry_with_id(Measurement, unique_id)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(
        error, action, url_for('routes_settings.settings_measurement'))


def settings_unit_add(form):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['add']['title'],
        controller=gettext("Unit"))
    error = []
    choices_unit = choices_units(Unit.query.all())

    if form.validate():
        name_safe = re.sub('[^0-9a-zA-Z]+', '_', form.id.data)
        if name_safe.endswith('_'):
            name_safe = name_safe[:-1]

        if name_safe in choices_unit:
            error.append("Unit name already exists: {name}".format(
                name=name_safe))

        new_unit = Unit()
        new_unit.name_safe = name_safe
        new_unit.name = form.name.data
        new_unit.unit = form.unit.data

        try:
            if not error:
                new_unit.save()
                flash(gettext(
                    "Unit with ID %(id)s (%(uuid)s) successfully added",
                    id=new_unit.id,
                    uuid=new_unit.unique_id),
                    "success")
        except sqlalchemy.exc.OperationalError as except_msg:
            error.append(except_msg)
        except sqlalchemy.exc.IntegrityError as except_msg:
            error.append(except_msg)

        flash_success_errors(
            error, action, url_for('routes_settings.settings_measurement'))
    else:
        flash_form_errors(form)


def settings_unit_mod(form):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['modify']['title'],
        controller=gettext("Unit"))
    error = []
    try:
        mod_unit = Unit.query.filter(
            Unit.unique_id == form.unit_id.data).first()

        name_safe = re.sub('[^0-9a-zA-Z]+', '_', form.id.data)
        if name_safe.endswith('_'):
            name_safe = name_safe[:-1]

        conversions = Conversion.query.filter(or_(
            Conversion.convert_unit_from == mod_unit.name_safe,
            Conversion.convert_unit_to == mod_unit.name_safe
        )).count()

        if (Unit.query.filter(
                and_(Unit.name_safe == name_safe,
                     Unit.unique_id != form.unit_id.data)).count() or
                name_safe in UNITS):
            error.append("Unit name already exists: {name}".format(
                name=name_safe))
        elif mod_unit.name_safe != name_safe:
            if conversions:
                error.append(
                    "Unit belongs to a conversion."
                    "Delete conversion(s) before changing unit.")
            else:
                # Ensure no Inputs depend on this measurement
                for _, each_data in parse_input_information().items():
                    if 'measurements_dict' in each_data:
                        for _, each_channel_data in each_data['measurements_dict'].items():
                            if ('unit' in each_channel_data and
                                    each_channel_data['unit'] == mod_unit.name_safe):
                                error.append(
                                    "Cannot change the name of this unit "
                                    "because an Input depends on it.")

        mod_unit.name = form.name.data
        mod_unit.unit = form.unit.data
        mod_unit.name_safe = name_safe

        if not error:
            db.session.commit()
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(
        error, action, url_for('routes_settings.settings_measurement'))


def settings_unit_del(unique_id):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['delete']['title'],
        controller=gettext("Unit"))
    error = []

    del_unit = Unit.query.filter(
        Unit.unique_id == unique_id).first()

    conversions = Conversion.query.filter(or_(
        Conversion.convert_unit_from == del_unit.name_safe,
        Conversion.convert_unit_to == del_unit.name_safe
    )).count()

    if conversions:
        error.append(
            "Unit belongs to a conversion."
            "Delete conversion(s) before deleting unit.")

    # Ensure no Inputs depend on this unit
    for _, each_data in parse_input_information().items():
        if 'measurements_dict' in each_data:
            for _, each_channel_data in each_data['measurements_dict'].items():
                if ('unit' in each_channel_data and
                        each_channel_data['unit'] == del_unit.name_safe):
                    error.append("Cannot delete this unit because an "
                                 "Input depends on it.")

    try:
        if not error:
            delete_entry_with_id(Unit, unique_id)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(
        error, action, url_for('routes_settings.settings_measurement'))


def settings_convert_add(form):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['add']['title'],
        controller=gettext("Conversion"))
    error = []

    conversion = Conversion.query.all()

    conversion_str = '{fr}_to_{to}'.format(
        fr=form.convert_unit_from.data, to=form.convert_unit_to.data)
    if conversion_str in all_conversions(conversion):
        error.append("Conversion '{cs}' already exists.".format(
            cs=conversion_str))

    if 'x' not in form.equation.data:
        error.append("'x' must appear in the equation.")

    if form.validate():
        new_conversion = Conversion()
        new_conversion.convert_unit_from = form.convert_unit_from.data
        new_conversion.convert_unit_to = form.convert_unit_to.data
        new_conversion.equation = form.equation.data

        try:
            if not error:
                new_conversion.save()
                flash(gettext(
                    "Conversion with ID %(id)s (%(uuid)s) successfully added",
                    id=new_conversion.id,
                    uuid=new_conversion.unique_id),
                    "success")
        except sqlalchemy.exc.OperationalError as except_msg:
            error.append(except_msg)
        except sqlalchemy.exc.IntegrityError as except_msg:
            error.append(except_msg)

        flash_success_errors(
            error, action, url_for('routes_settings.settings_measurement'))
    else:
        flash_form_errors(form)


def settings_convert_mod(form):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['modify']['title'],
        controller=gettext("Conversion"))
    error = []

    if 'x' not in form.equation.data:
        error.append("'x' must appear in the equation")

    try:
        mod_conversion = Conversion.query.filter(
            Conversion.unique_id == form.conversion_id.data).first()

        # Don't allow conversion to be changed for an active controller
        error = check_conversion_being_used(mod_conversion, error, state='active')

        if not error:
            # Don't allow from conversion to be changed for an inactive controller
            if mod_conversion.convert_unit_from != form.convert_unit_from.data:
                error = check_conversion_being_used(mod_conversion, error, state='inactive')

            if not mod_conversion.protected:
                mod_conversion.convert_unit_from = form.convert_unit_from.data
                mod_conversion.convert_unit_to = form.convert_unit_to.data
            mod_conversion.equation = form.equation.data
            db.session.commit()
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(
        error, action, url_for('routes_settings.settings_measurement'))


def settings_convert_del(unique_id):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['delete']['title'],
        controller=gettext("Conversion"))
    error = []

    try:
        conv = Conversion.query.filter(
            Conversion.unique_id == unique_id).first()

        # Don't allow conversion to be changed for an active controller
        error = check_conversion_being_used(conv, error, state='active')

        if not error:
            # Delete conversion from any controllers
            remove_conversion_from_controllers(unique_id)
            delete_entry_with_id(Conversion, unique_id)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(
        error, action, url_for('routes_settings.settings_measurement'))


def check_conversion_being_used(conv, error, state=None):
    """
    Check if a controller is currently active/inactive and using the conversion
    If so, cannot edit the database/modify the conversion
    """
    try:
        device_measurements = DeviceMeasurements.query.all()

        list_measurements = [Input, PID,]

        for each_device_type in list_measurements:
            for each_device in each_device_type.query.all():
                for each_meas in device_measurements:
                    if (each_device.unique_id == each_meas.device_id and
                            conv.unique_id == each_meas.conversion_id):

                        detected_device = each_device_type.query.filter(
                            each_device_type.unique_id == each_meas.device_id).first()

                        if ((state == 'active' and detected_device.is_activated) or
                                (state == 'inactive' and not detected_device.is_activated)):
                            error.append(
                                "Conversion [{cid}] ({conv}): "
                                "Currently in use for measurement {meas}, "
                                "for device {dev}".format(
                                    cid=conv.id,
                                    conv=conv.unique_id,
                                    meas=each_meas.unique_id,
                                    dev=each_meas.device_id))
    except Exception as except_msg:
        error.append(except_msg)
    return error


def remove_conversion_from_controllers(conv_id):
    """
    Find measurements using the conversion and delete the reference to the conversion_id
    """
    device_measurements = DeviceMeasurements.query.all()

    for each_meas in device_measurements:
        if each_meas.conversion_id == conv_id:
            each_meas.conversion_id = ''

    db.session.commit()


def settings_pi_mod(form):
    """
    Change Pi Settings
    Commands found at
    https://github.com/raspberrypi-ui/rc_gui/blob/master/src/rc_gui.c
    """
    error = []
    status = None
    action_str = None

    if form.enable_i2c.data:
        _, _, status = cmd_output("raspi-config nonint do_i2c 0", user='root')
        action_str = "Enable I2C"
    elif form.disable_i2c.data:
        _, _, status = cmd_output("raspi-config nonint do_i2c 1", user='root')
        action_str = "Disable I2C"
    elif form.enable_one_wire.data:
        _, _, status = cmd_output("raspi-config nonint do_onewire 0", user='root')
        action_str = "Enable 1-Wire"
    elif form.disable_one_wire.data:
        _, _, status = cmd_output("raspi-config nonint do_onewire 1", user='root')
        action_str = "Disable 1-Wire"
    elif form.enable_serial.data:
        _, _, status = cmd_output("raspi-config nonint do_serial 0", user='root')
        action_str = "Enable Serial"
    elif form.disable_serial.data:
        _, _, status = cmd_output("raspi-config nonint do_serial 1", user='root')
        action_str = "Disable Serial"
    elif form.enable_spi.data:
        _, _, status = cmd_output("raspi-config nonint do_spi 0", user='root')
        action_str = "Enable SPI"
    elif form.disable_spi.data:
        _, _, status = cmd_output("raspi-config nonint do_spi 1", user='root')
        action_str = "Disable SPI"
    elif form.enable_ssh.data:
        _, _, status = cmd_output("raspi-config nonint do_ssh 0", user='root')
        action_str = "Enable SSH"
    elif form.disable_ssh.data:
        _, _, status = cmd_output("raspi-config nonint do_ssh 1", user='root')
        action_str = "Disable SSH"
    elif form.change_hostname.data:
        if is_valid_hostname(form.hostname.data):
            _, _, status = cmd_output(
                "raspi-config nonint do_hostname {host}".format(
                    host=form.hostname.data))
        else:
            error.append(
                "Invalid hostname. Hostnames are composed of series of "
                "labels concatenated with dots, as are all domain names. "
                "Hostnames must be 1 to 63 characters and may contain only "
                "the ASCII letters 'a' through 'z' (in a case-insensitive "
                "manner), the digits '0' through '9', and the hyphen ('-').")
        action_str = "Change Hostname to '{host}'".format(
            host=form.hostname.data)
    elif form.change_pigpiod_sample_rate.data:
        if form.pigpiod_sample_rate.data not in ['low', 'high', 'disabled', 'uninstalled']:
            error.append(
                "Valid pigpiod options: Uninstall, Disable, 1 ms, or 5 ms. "
                "Invalid option: {op}".format(
                    op=form.pigpiod_sample_rate.data))
        else:
            # Stop the Mycodo daemon
            cmd = f"{INSTALL_DIRECTORY}/mycodo/scripts/mycodo_wrapper daemon_stop" \
                  f" | ts '[%Y-%m-%d %H:%M:%S]' 2>&1"
            stop_daemon = subprocess.Popen(cmd, shell=True)
            stop_daemon.wait()

            if (form.pigpiod_sample_rate.data != 'uninstalled' and
                    form.pigpiod_state.data == 'uninstalled'):
                # Install pigpiod (sample rate of 1 ms)
                cmd = f"{INSTALL_DIRECTORY}/mycodo/scripts/mycodo_wrapper install_pigpiod" \
                      f" | ts '[%Y-%m-%d %H:%M:%S]' 2>&1"
                install_pigpiod = subprocess.Popen(cmd, shell=True)
                install_pigpiod.wait()

            # Disable pigpiod
            cmd = f"{INSTALL_DIRECTORY}/mycodo/scripts/mycodo_wrapper disable_pigpiod" \
                  f" | ts '[%Y-%m-%d %H:%M:%S]' 2>&1"
            disable_pigpiod = subprocess.Popen(cmd, shell=True)
            disable_pigpiod.wait()

            if form.pigpiod_sample_rate.data == 'low':
                # Install pigpiod (sample rate of 1 ms)
                cmd = f"{INSTALL_DIRECTORY}/mycodo/scripts/mycodo_wrapper enable_pigpiod_low" \
                      f" | ts '[%Y-%m-%d %H:%M:%S]' 2>&1"
                enable_pigpiod_1ms = subprocess.Popen(cmd, shell=True)
                enable_pigpiod_1ms.wait()
            elif form.pigpiod_sample_rate.data == 'high':
                # Install pigpiod (sample rate of 5 ms)
                cmd = f"{INSTALL_DIRECTORY}/mycodo/scripts/mycodo_wrapper enable_pigpiod_high" \
                      f" | ts '[%Y-%m-%d %H:%M:%S]' 2>&1"
                enable_pigpiod_5ms = subprocess.Popen(cmd, shell=True)
                enable_pigpiod_5ms.wait()
            elif form.pigpiod_sample_rate.data == 'disabled':
                # Disable pigpiod (user selected disable)
                cmd = f"{INSTALL_DIRECTORY}/mycodo/scripts/mycodo_wrapper enable_pigpiod_disabled" \
                      f" | ts '[%Y-%m-%d %H:%M:%S]' 2>&1"
                disable_pigpiod = subprocess.Popen(cmd, shell=True)
                disable_pigpiod.wait()
            elif form.pigpiod_sample_rate.data == 'uninstalled':
                # Uninstall pigpiod (user selected disable)
                cmd = f"{INSTALL_DIRECTORY}/mycodo/scripts/mycodo_wrapper uninstall_pigpiod" \
                      f" | ts '[%Y-%m-%d %H:%M:%S]' 2>&1"
                uninstall_pigpiod = subprocess.Popen(cmd, shell=True)
                uninstall_pigpiod.wait()

            # Start the Mycodo daemon
            cmd = f"{INSTALL_DIRECTORY}/mycodo/scripts/mycodo_wrapper daemon_start" \
                  f" | ts '[%Y-%m-%d %H:%M:%S]' 2>&1"
            start_daemon = subprocess.Popen(cmd, shell=True)
            start_daemon.wait()

    if status:
        error.append("Unknown error executing command to {action}".format(
            action=action_str))

    action = '{controller}: {action}'.format(
        controller=gettext("Pi Settings"),
        action=action_str)

    flash_success_errors(error, action, url_for('routes_settings.settings_pi'))


def settings_alert_mod(form_mod_alert):
    """Modify Alert settings."""
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['modify']['title'],
        controller=gettext("Alert Settings"))
    error = []

    try:
        if form_mod_alert.validate():
            mod_smtp = SMTP.query.one()
            if form_mod_alert.send_test.data:
                send_email(
                    mod_smtp.host, mod_smtp.protocol, mod_smtp.port,
                    mod_smtp.user, mod_smtp.passw, mod_smtp.email_from,
                    form_mod_alert.send_test_to_email.data,
                    "This is a test email from Mycodo")
                flash(gettext("Test email sent to %(recip)s. Check your "
                              "inbox to see if it was successful.",
                              recip=form_mod_alert.send_test_to_email.data),
                      "success")
                return redirect(url_for('routes_settings.settings_alerts'))
            else:
                mod_smtp.host = form_mod_alert.smtp_host.data
                if form_mod_alert.smtp_port.data:
                    mod_smtp.port = form_mod_alert.smtp_port.data
                else:
                    mod_smtp.port = None
                mod_smtp.protocol = form_mod_alert.smtp_protocol.data
                mod_smtp.user = form_mod_alert.smtp_user.data
                if form_mod_alert.smtp_password.data:
                    mod_smtp.passw = form_mod_alert.smtp_password.data
                mod_smtp.email_from = form_mod_alert.smtp_from_email.data
                mod_smtp.hourly_max = form_mod_alert.smtp_hourly_max.data
                db.session.commit()
        else:
            flash_form_errors(form_mod_alert)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(
        error, action, url_for('routes_settings.settings_alerts'))


def settings_diagnostic_delete_inputs():
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['delete']['title'],
        controller=TRANSLATIONS['input']['title'])
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }

    inputs = db_retrieve_table(Input)
    device_measurements = db_retrieve_table(DeviceMeasurements)
    display_order = db_retrieve_table(DisplayOrder, entry='first')

    if not messages["error"]:
        try:
            for each_input in inputs:
                # Deactivate any active controllers using the input
                if each_input.is_activated:
                    # messages = input_deactivate_associated_controllers(
                    #     messages, each_input.unique_id)
                    messages = controller_activate_deactivate(
                        messages, 'deactivate', 'Input', each_input.unique_id)

                # Delete all measurements associated with the input
                for each_measurement in device_measurements:
                    if each_measurement.device_id == each_input.unique_id:
                        db.session.delete(each_measurement)

                # Delete the input
                db.session.delete(each_input)
            display_order.input = ''  # Clear the order
            db.session.commit()
        except Exception as except_msg:
            messages["error"].append(str(except_msg))

    flash_success_errors(
        messages["error"],
        action,
        url_for('routes_settings.settings_diagnostic'))


def settings_diagnostic_delete_dashboard_elements():
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['delete']['title'],
        controller=TRANSLATIONS['dashboard']['title'])
    error = []

    dashboard = db_retrieve_table(Dashboard)
    widget = db_retrieve_table(Widget)

    if not error:
        try:
            for each_dash in dashboard:
                db.session.delete(each_dash)
                db.session.commit()

            for each_widget in widget:
                db.session.delete(each_widget)
                db.session.commit()

            Dashboard(id=1, name='Default').save()
        except Exception as except_msg:
            error.append(except_msg)

    flash_success_errors(
        error, action, url_for('routes_settings.settings_diagnostic'))


def settings_diagnostic_delete_notes_tags():
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['delete']['title'],
        controller='{}/{}'.format(TRANSLATIONS['tag']['title'],
                                  TRANSLATIONS['note']['title']))
    error = []

    if not error:
        try:
            for each_tag in db_retrieve_table(NoteTags):
                db.session.delete(each_tag)
                db.session.commit()
            for each_note in db_retrieve_table(Notes):
                db.session.delete(each_note)
                db.session.commit()
        except Exception as except_msg:
            error.append(except_msg)

    flash_success_errors(
        error, action, url_for('routes_settings.settings_diagnostic'))


def settings_diagnostic_delete_outputs():
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['delete']['title'],
        controller=TRANSLATIONS['output']['title'])
    error = []

    output = db_retrieve_table(Output)
    output_channels = db_retrieve_table(OutputChannel)
    display_order = db_retrieve_table(DisplayOrder, entry='first')

    if not error:
        try:
            for each_output in output:
                channels = output_channels.filter(
                    OutputChannel.output_id == each_output.unique_id)
                for each_output_channel in channels:
                    db.session.delete(each_output_channel)

                db.session.delete(each_output)
                db.session.commit()
            display_order.output = ''
            db.session.commit()
        except Exception as except_msg:
            error.append(except_msg)

    flash_success_errors(
        error, action, url_for('routes_settings.settings_diagnostic'))


def settings_diagnostic_delete_settings_database():
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['delete']['title'],
        controller='Settings Database')
    error = []

    if not error:
        try:
            os.remove('/opt/Mycodo/databases/mycodo.db')
            cmd = "{pth}/mycodo/scripts/mycodo_wrapper frontend_reload" \
                  " | ts '[%Y-%m-%d %H:%M:%S]'" \
                  " >> {log} 2>&1".format(pth=INSTALL_DIRECTORY,
                                          log=DAEMON_LOG_FILE)
            subprocess.Popen(cmd, shell=True)
        except Exception as except_msg:
            error.append(except_msg)

    flash_success_errors(
        error, action, url_for('routes_settings.settings_diagnostic'))


def settings_diagnostic_delete_file(delete_type):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['delete']['title'],
        controller=gettext("File"))
    error = []

    if not error:
        try:
            file_remove = None
            if delete_type == 'dependency':
                file_remove = os.path.abspath(DEPENDENCY_INIT_FILE)
            elif delete_type == 'upgrade':
                file_remove = os.path.abspath(UPGRADE_INIT_FILE)
            if file_remove:
                if os.path.isfile(file_remove):
                    os.remove(file_remove)
                else:
                    error.append("File not found: {}".format(file_remove))
            else:
                error.append("Unknown file: {}".format(delete_type))
        except Exception as except_msg:
            error.append(except_msg)

    flash_success_errors(
        error, action, url_for('routes_settings.settings_diagnostic'))


def settings_diagnostic_recreate_influxdb_db_1():
    action = gettext("Recreate InfluxDB 1.x Database")
    error = []

    if not error:
        try:
            command = f'/bin/bash {INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh recreate-influxdb-1-db'
            p = subprocess.Popen(command, shell=True)
            p.communicate()
        except Exception:
            logger.exception()
    
    flash_success_errors(
        error, action, url_for('routes_settings.settings_diagnostic'))


def settings_diagnostic_recreate_influxdb_db_2():
    action = gettext("Recreate InfluxDB 2.x Database")
    error = []

    if not error:
        try:
            command = f'/bin/bash {INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh recreate-influxdb-2-db'
            p = subprocess.Popen(command, shell=True)
            p.communicate()
        except Exception:
            logger.exception()
    
    flash_success_errors(
        error, action, url_for('routes_settings.settings_diagnostic'))


def settings_diagnostic_reset_email_counter():
    action = gettext("Reset Email Counter")
    error = []

    if not error:
        try:
            smtp_settings = SMTP.query.first()
            smtp_settings.email_count = 0
            smtp_settings.smtp_wait_timer = time.time() + 3600
            db.session.commit()
        except Exception as except_msg:
            error.append(except_msg)

    flash_success_errors(
        error, action, url_for('routes_settings.settings_diagnostic'))


def settings_diagnostic_install_dependencies():
    action = gettext("Install Dependencies")
    error = []

    if not error:
        try:
            def install_dependencies():
                cmd = "{pth}/mycodo/scripts/mycodo_wrapper update_dependencies" \
                      " | ts '[%Y-%m-%d %H:%M:%S]' >> {log} 2>&1".format(
                    pth=INSTALL_DIRECTORY,
                    log=DEPENDENCY_LOG_FILE)
                _, _, _ = cmd_output(cmd, user="root")

                cmd = "{pth}/mycodo/scripts/mycodo_wrapper frontend_restart" \
                      " | ts '[%Y-%m-%d %H:%M:%S]' >> {log} 2>&1".format(
                    pth=INSTALL_DIRECTORY,
                    log=DEPENDENCY_LOG_FILE)
                _, _, _ = cmd_output(cmd, user="root")

                cmd = "{pth}/mycodo/scripts/mycodo_wrapper daemon_restart" \
                      " | ts '[%Y-%m-%d %H:%M:%S]' >> {log} 2>&1".format(
                    pth=INSTALL_DIRECTORY,
                    log=DEPENDENCY_LOG_FILE)
                _, _, _ = cmd_output(cmd, user="root")

            install_deps = threading.Thread(target=install_dependencies)
            install_deps.start()
        except Exception as except_msg:
            error.append(except_msg)

    flash("Installation of dependencies has been initiated. "
          "This can take a while. You can view the progress in the Dependency Log. "
          "At completion, the frontend and backend will be restarted.", "success")
    flash_success_errors(
        error, action, url_for('routes_settings.settings_diagnostic'))


def settings_regenerate_widget_html():
    try:
        time.sleep(2)

        cmd = f'/bin/bash {INSTALL_DIRECTORY}/mycodo/scripts/upgrade_commands.sh generate-widget-html'
        out, err, status = cmd_output(cmd, stdout_pipe=False, user='root')
        logger.info(
            "Regenerate Widget HTML: "
            f"cmd: {cmd}; out: {out}; error: {err}; status: {status}")

        logger.info("Reloading frontend in 10 seconds")
        cmd = f"sleep 10 && {INSTALL_DIRECTORY}/mycodo/scripts/mycodo_wrapper frontend_reload 2>&1"
        subprocess.Popen(cmd, shell=True)
    except Exception:
        logger.exception("Regenerating widget HTML")


def settings_diagnostic_upgrade_master():
    action = gettext("Set to Upgrade to Master")
    error = []

    if not error:
        try:
            path_config = os.path.join(INSTALL_DIRECTORY, "mycodo/config.py")

            if not os.path.exists(path_config):
                logger.error(f"Path doesn't exist: {path_config}")
                return

            with open(path_config) as fin, NamedTemporaryFile(dir='.', delete=False) as fout:
                for line in fin:
                    if line.startswith("FORCE_UPGRADE_MASTER = False"):
                        line = "FORCE_UPGRADE_MASTER = True\n"
                    fout.write(line.encode('utf8'))
                os.rename(fout.name, path_config)
            os.chmod(path_config, stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH)
            set_user_grp(path_config, 'mycodo', 'mycodo')
            flash_success_errors(
                error, action, url_for('routes_settings.settings_diagnostic'))
            return
        except Exception as except_msg:
            error.append(except_msg)
            flash_success_errors(
                error, action, url_for('routes_settings.settings_diagnostic'))
            return
        finally:
            command = '/bin/bash {path}/mycodo/scripts/upgrade_commands.sh web-server-restart'.format(
                path=INSTALL_DIRECTORY)
            subprocess.Popen(command, shell=True)


def is_valid_hostname(hostname):
    if len(hostname) > 255:
        return False
    if hostname[-1] == ".":
        hostname = hostname[:-1] # strip exactly one dot from the right, if present
    allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
    return all(allowed.match(x) for x in hostname.split("."))
