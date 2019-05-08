# -*- coding: utf-8 -*-
import logging

import sqlalchemy
from flask import flash
from flask import url_for
from flask_babel import gettext

from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import Actions
from mycodo.databases.models import DisplayOrder
from mycodo.databases.models import Trigger
from mycodo.mycodo_client import DaemonControl
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.utils.utils_function import check_actions
from mycodo.mycodo_flask.utils.utils_general import controller_activate_deactivate
from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.mycodo_flask.utils.utils_general import flash_success_errors
from mycodo.utils.system_pi import csv_to_list_of_str
from mycodo.utils.system_pi import epoch_of_next_time
from mycodo.utils.system_pi import list_to_csv

logger = logging.getLogger(__name__)
logger = logging.LoggerAdapter(
    logger, {'name_info': 'Trigger'})


def trigger_mod(form):
    """Modify a Trigger"""
    error = []
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['modify']['title'],
        controller=TRANSLATIONS['trigger']['title'])

    try:
        trigger = Trigger.query.filter(
            Trigger.unique_id == form.function_id.data).first()
        trigger.name = form.name.data
        trigger.log_level_debug = form.log_level_debug.data

        if trigger.trigger_type == 'trigger_edge':
            error = check_form_edge(form, error)
            trigger.measurement = form.measurement.data
            trigger.edge_detected = form.edge_detected.data

        elif trigger.trigger_type == 'trigger_output':
            error = check_form_output(form, error)
            trigger.unique_id_1 = form.unique_id_1.data
            trigger.output_state = form.output_state.data
            trigger.output_duration = form.output_duration.data

        elif trigger.trigger_type == 'trigger_output_pwm':
            error = check_form_output_pwm(form, error)
            trigger.unique_id_1 = form.unique_id_1.data
            trigger.output_state = form.output_state.data
            trigger.output_duty_cycle = form.output_duty_cycle.data

        elif trigger.trigger_type == 'trigger_run_pwm_method':
            error = check_form_run_pwm_method(form, error)
            trigger.unique_id_1 = form.unique_id_1.data
            trigger.unique_id_2 = form.unique_id_2.data
            trigger.period = form.period.data
            trigger.trigger_actions_at_start = form.trigger_actions_at_start.data
            trigger.trigger_actions_at_period = form.trigger_actions_at_period.data

        elif trigger.trigger_type == 'trigger_infrared_remote_input':
            error = check_form_infrared_remote_input(form, error)
            trigger.program = form.program.data
            trigger.word = form.word.data

        elif trigger.trigger_type == 'trigger_sunrise_sunset':
            error = check_form_sunrise_sunset(form, error)
            trigger.rise_or_set = form.rise_or_set.data
            trigger.latitude = form.latitude.data
            trigger.longitude = form.longitude.data
            trigger.zenith = form.zenith.data
            trigger.date_offset_days = form.date_offset_days.data
            trigger.time_offset_minutes = form.time_offset_minutes.data

        elif trigger.trigger_type == 'trigger_timer_daily_time_point':
            error = check_form_timer_daily_time_point(form, error)
            trigger.timer_start_time = form.timer_start_time.data

        elif trigger.trigger_type == 'trigger_timer_daily_time_span':
            error = check_form_timer_daily_time_span(form, error)
            trigger.period = form.period.data
            trigger.timer_start_time = form.timer_start_time.data
            trigger.timer_end_time = form.timer_end_time.data

        elif trigger.trigger_type == 'trigger_timer_duration':
            error = check_form_timer_duration(form, error)
            trigger.period = form.period.data
            trigger.timer_start_offset = form.timer_start_offset.data

        if not error:
            db.session.commit()

            if trigger.is_activated:
                control = DaemonControl()
                return_value = control.refresh_daemon_trigger_settings(
                    form.function_id.data)
                flash(gettext(
                    "Daemon response: %(resp)s",
                    resp=return_value), "success")

    except sqlalchemy.exc.OperationalError as except_msg:
        error.append(except_msg)
    except sqlalchemy.exc.IntegrityError as except_msg:
        error.append(except_msg)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def trigger_del(trigger_id):
    """Delete a Trigger"""
    error = []
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['delete']['title'],
        controller=TRANSLATIONS['trigger']['title'])

    trigger = Trigger.query.filter(
        Trigger.unique_id == trigger_id).first()

    # Deactivate trigger if active
    if trigger.is_activated:
        trigger_deactivate(trigger_id)

    try:
        if not error:
            # Delete Actions
            actions = Actions.query.filter(
                Actions.function_id == trigger_id).all()
            for each_action in actions:
                delete_entry_with_id(Actions,
                                     each_action.unique_id)

            delete_entry_with_id(Trigger, trigger_id)

            display_order = csv_to_list_of_str(DisplayOrder.query.first().function)
            display_order.remove(trigger_id)
            DisplayOrder.query.first().function = list_to_csv(display_order)
            db.session.commit()
    except sqlalchemy.exc.OperationalError as except_msg:
        error.append(except_msg)
    except sqlalchemy.exc.IntegrityError as except_msg:
        error.append(except_msg)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def trigger_activate(trigger_id):
    """Activate a Trigger"""
    error = []
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['activate']['title'],
        controller=TRANSLATIONS['trigger']['title'])

    mod_trigger = Trigger.query.filter(
        Trigger.unique_id == trigger_id).first()

    # Check for errors in the Trigger settings
    if mod_trigger.trigger_type == 'edge':
        error = check_cond_edge(mod_trigger, error)
    elif mod_trigger.trigger_type == 'output':
        error = check_cond_output(mod_trigger, error)

    actions = Actions.query.filter(
        Actions.function_id == trigger_id)

    if not actions.count():
        error.append("No Actions found: Add at least one Action before activating.")

    for each_action in actions.all():
        error = check_actions(each_action, error)

    if mod_trigger.trigger_type == 'run_pwm_method':
        mod_trigger_ready = Trigger.query.filter(
            Trigger.unique_id == trigger_id).first()
        mod_trigger_ready.method_start_time = 'Ready'
        db.session.commit()

    if not error:
        controller_activate_deactivate(
            'activate',
            'Trigger',
            trigger_id)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def trigger_deactivate(trigger_id):
    """Deactivate a Trigger"""
    error = []
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['deactivate']['title'],
        controller=TRANSLATIONS['trigger']['title'])

    if not error:
        controller_activate_deactivate(
            'deactivate',
            'Trigger',
            trigger_id)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def check_form_edge(form, error):
    """Checks if the submitted form has any errors"""
    if not form.measurement.data or form.measurement.data == '':
        error.append("{meas} must be set".format(
            meas=form.measurement.label.text))
    return error


def check_cond_edge(form, error):
    """Checks if the saved variables have any errors"""
    if not form.measurement or form.measurement == '':
        error.append("Measurement must be set")
    return error


def check_form_output(form, error):
    """Checks if the submitted form has any errors"""
    if not form.unique_id_1.data:
        error.append("{id} must be set".format(
            id=form.unique_id_1.label.text))
    if not form.output_state.data:
        error.append("{id} must be set".format(
            id=form.output_state.label.text))
    return error


def check_form_output_duration(form, error):
    """Checks if the submitted form has any errors"""
    if not form.unique_id_1.data:
        error.append("{id} must be set".format(
            id=form.unique_id_1.label.text))
    if not form.output_state.data:
        error.append("{id} must be set".format(
            id=form.output_state.label.text))
    if not form.output_duration.data:
        error.append("{id} must be set".format(
            id=form.output_duration.label.text))
    return error


def check_form_output_pwm(form, error):
    """Checks if the submitted form has any errors"""
    if not form.unique_id_1.data:
        error.append("{id} must be set".format(
            id=form.unique_id_1.label.text))
    if not form.output_state or form.output_state == '':
        error.append("State must be set".format(
            dir=form.output_state))
    if not 0 <= form.output_duty_cycle.data <= 100:
        error.append("{id} must >= 0 and <= 100".format(
            id=form.output_duty_cycle.label.text))
    return error


def check_form_run_pwm_method(form, error):
    """Checks if the saved variables have any errors"""
    if not form.period.data or form.period.data <= 0:
        error.append("Period must be greater than 0")
    if not form.unique_id_1.data:
        error.append("{id} must be set".format(
            id=form.unique_id_1.label.text))
    if not form.unique_id_2.data:
        error.append("{id} must be set".format(
            id=form.unique_id_2.label.text))
    return error


def check_form_infrared_remote_input(form, error):
    """Checks if the submitted form has any errors"""
    if not form.program.data:
        error.append("{id} must be set".format(
            id=form.program.label.text))
    if not form.word.data:
        error.append("{id} must be set".format(
            id=form.program.label.text))
    return error


def check_form_sunrise_sunset(form, error):
    """Checks if the submitted form has any errors"""
    if form.rise_or_set.data not in ['sunrise', 'sunset']:
        error.append("{id} must be set to 'sunrise' or 'sunset'".format(
            id=form.rise_or_set.label.text))
    if -90 > form.latitude.data > 90:
        error.append("{id} must be >= -90 and <= 90".format(
            id=form.latitude.label.text))
    if -180 > form.longitude.data > 180:
        error.append("{id} must be >= -180 and <= 180".format(
            id=form.longitude.label.text))
    if form.zenith.data is None:
        error.append("{id} must be set".format(
            id=form.zenith.label.text))
    if form.date_offset_days.data is None:
        error.append("{id} must be set".format(
            id=form.date_offset_days.label.text))
    if form.time_offset_minutes.data is None:
        error.append("{id} must be set".format(
            id=form.time_offset_minutes.label.text))
    return error


def check_form_timer_daily_time_point(form, error):
    """Checks if the submitted form has any errors"""
    if not epoch_of_next_time('{hm}:00'.format(hm=form.timer_start_time.data)):
        error.append("{id} must be a valid HH:MM time format".format(
            id=form.timer_start_time.label.text))
    return error


def check_form_timer_daily_time_span(form, error):
    """Checks if the submitted form has any errors"""
    if not epoch_of_next_time('{hm}:00'.format(hm=form.timer_start_time.data)):
        error.append("{id} must be a valid HH:MM time format".format(
            id=form.timer_start_time.label.text))
    if not epoch_of_next_time('{hm}:00'.format(hm=form.timer_end_time.data)):
        error.append("{id} must be a valid HH:MM time format".format(
            id=form.timer_end_time.label.text))
    return error


def check_form_timer_duration(form, error):
    """Checks if the submitted form has any errors"""
    if form.period.data <= 0:
        error.append("{id} must be > 0".format(
            id=form.period.label.text))
    if form.timer_start_offset.data < 0:
        error.append("{id} must be >= 0".format(
            id=form.timer_start_offset.label.text))
    return error


def check_cond_output(form, error):
    """Checks if the saved variables have any errors"""
    if not form.unique_id_1 or form.unique_id_1 == '':
        error.append("An Output must be set")
    if not form.output_state or form.output_state == '':
        error.append("A State must be set")
    return error
