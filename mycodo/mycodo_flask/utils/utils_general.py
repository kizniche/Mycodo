# -*- coding: utf-8 -*-
import logging
import sqlalchemy
import flask_login
from collections import OrderedDict
from datetime import datetime

from flask import flash
from flask import redirect
from flask import url_for

from mycodo.mycodo_flask.extensions import db
from flask_babel import gettext

from mycodo.mycodo_client import DaemonControl

from mycodo.databases.models import Input
from mycodo.databases.models import LCD
from mycodo.databases.models import Math
from mycodo.databases.models import PID
from mycodo.databases.models import Role
from mycodo.databases.models import Timer
from mycodo.databases.models import User

from mycodo.config import MEASUREMENT_UNITS
from mycodo.config import MEASUREMENTS

logger = logging.getLogger(__name__)


#
# Activate/deactivate controller
#

def controller_activate_deactivate(controller_action,
                                   controller_type,
                                   controller_id):
    """
    Activate or deactivate controller

    :param controller_action: Activate or deactivate
    :type controller_action: str
    :param controller_type: The controller type (LCD, Math, PID, Input, Timer)
    :type controller_type: str
    :param controller_id: Controller with ID to activate or deactivate
    :type controller_id: str
    """
    if not user_has_permission('edit_controllers'):
        return redirect(url_for('general_routes.home'))

    activated = bool(controller_action == 'activate')

    translated_names = {
        "Input": gettext(u"Input"),
        "LCD": gettext(u"LCD"),
        "Math": gettext(u"Math"),
        "PID": gettext(u"PID"),
        "Timer": gettext(u"Timer")
    }

    mod_controller = None
    if controller_type == 'Input':
        mod_controller = Input.query.filter(
            Input.id == int(controller_id)).first()
    elif controller_type == 'LCD':
        mod_controller = LCD.query.filter(
            LCD.id == int(controller_id)).first()
    elif controller_type == 'Math':
        mod_controller = Math.query.filter(
            Math.id == int(controller_id)).first()
    elif controller_type == 'PID':
        mod_controller = PID.query.filter(
            PID.id == int(controller_id)).first()
    elif controller_type == 'Timer':
        mod_controller = Timer.query.filter(
            Timer.id == int(controller_id)).first()

    if mod_controller is None:
        flash("{type} Controller {id} doesn't exist".format(
            type=controller_type, id=controller_id), "error")
        return redirect(url_for('general_routes.home'))

    try:
        mod_controller.is_activated = activated
        db.session.commit()

        if activated:
            flash(gettext(u"%(cont)s controller activated in SQL database",
                          cont=translated_names[controller_type]),
                  "success")
        else:
            flash(gettext(u"%(cont)s controller deactivated in SQL database",
                          cont=translated_names[controller_type]),
                  "success")
    except Exception as except_msg:
        flash(gettext(u"Error: %(err)s",
                      err=u'SQL: {msg}'.format(msg=except_msg)),
              "error")

    try:
        control = DaemonControl()
        if controller_action == 'activate':
            return_values = control.controller_activate(controller_type,
                                                        int(controller_id))
        else:
            return_values = control.controller_deactivate(controller_type,
                                                          int(controller_id))
        if return_values[0]:
            flash("{err}".format(err=return_values[1]), "error")
        else:
            flash("{err}".format(err=return_values[1]), "success")
    except Exception as except_msg:
        flash(gettext(u"Error: %(err)s",
                      err=u'Daemon: {msg}'.format(msg=except_msg)),
              "error")


#
# Choices
#

def choices_inputs(inputs):
    """ populate form multi-select choices from Input entries """
    choices = OrderedDict()
    for each_input in inputs:
        if each_input.device == 'LinuxCommand':
            value = '{id},{meas}'.format(
                id=each_input.unique_id,
                meas=each_input.cmd_measurement)
            display = u'[Input {id:02d}] {name} ({meas})'.format(
                id=each_input.id,
                name=each_input.name,
                meas=each_input.cmd_measurement)
            choices.update({value: display})
        else:
            for each_measurement in MEASUREMENTS[each_input.device]:
                value = '{id},{meas}'.format(
                    id=each_input.unique_id,
                    meas=each_measurement)
                display = u'[Input {id:02d}] {name} ({meas})'.format(
                    id=each_input.id,
                    name=each_input.name,
                    meas=MEASUREMENT_UNITS[each_measurement]['name'])
                choices.update({value: display})
            # Display custom converted units for ADCs
            if each_input.device in ['ADS1x15', 'MCP342x']:
                value = '{id},{meas}'.format(
                    id=each_input.unique_id,
                    meas=each_input.adc_measure)
                display = u'[Input {id:02d}] {name} ({meas})'.format(
                    id=each_input.id,
                    name=each_input.name,
                    meas=each_input.adc_measure)
                choices.update({value: display})
    return choices


def choices_maths(maths):
    """ populate form multi-select choices from Math entries """
    choices = OrderedDict()
    for each_math in maths:
        for each_measurement in each_math.measure.split(','):
            value = '{id},{measure}'.format(
                id=each_math.unique_id,
                measure=each_measurement)

            if each_measurement in MEASUREMENT_UNITS:
                measurement_display = MEASUREMENT_UNITS[each_measurement]['name']
            else:
                measurement_display = each_measurement
            display = u'[Math {id:02d}] {name} ({meas})'.format(
                id=each_math.id,
                name=each_math.name,
                meas=measurement_display)
            choices.update({value: display})
    return choices


def choices_outputs(output):
    """ populate form multi-select choices from Output entries """
    choices = OrderedDict()
    for each_output in output:
        if each_output.relay_type != 'pwm':
            value = '{id},duration_sec'.format(id=each_output.unique_id)
            display = u'[Output {id:02d}] {name} (Duration)'.format(
                id=each_output.id, name=each_output.name)
            choices.update({value: display})
        elif each_output.relay_type == 'pwm':
            value = '{id},duty_cycle'.format(id=each_output.unique_id)
            display = u'[Output {id:02d}] {name} (Duty Cycle)'.format(
                id=each_output.id, name=each_output.name)
            choices.update({value: display})
    return choices


def choices_pids(pid):
    """ populate form multi-select choices from PID entries """
    choices = OrderedDict()
    for each_pid in pid:
        value = '{id},setpoint'.format(id=each_pid.unique_id)
        display = u'[PID {id:02d}] {name} (Setpoint)'.format(
            id=each_pid.id, name=each_pid.name)
        choices.update({value: display})
        value = '{id},pid_output'.format(id=each_pid.unique_id)
        display = u'[PID {id:02d}] {name} (Output Duration)'.format(
            id=each_pid.id, name=each_pid.name)
        choices.update({value: display})
        value = '{id},duty_cycle'.format(id=each_pid.unique_id)
        display = u'[PID {id:02d}] {name} (Output Duty Cycle)'.format(
            id=each_pid.id, name=each_pid.name)
        choices.update({value: display})
    return choices


def choices_id_name(table):
    """ Return a dictionary of all available ids and names of a table """
    choices = OrderedDict()
    for each_entry in table:
        value = each_entry.unique_id
        display = u'[{id:02d}] {name}'.format(id=each_entry.id,
                                          name=each_entry.name)
        choices.update({value: display})
    return choices


def user_has_permission(permission):
    user = User.query.filter(User.name == flask_login.current_user.name).first()
    role = Role.query.filter(Role.id == user.role).first()
    if ((permission == 'edit_settings' and role.edit_settings) or
        (permission == 'edit_controllers' and role.edit_controllers) or
        (permission == 'edit_users' and role.edit_users) or
        (permission == 'view_settings' and role.view_settings) or
        (permission == 'view_camera' and role.view_camera) or
        (permission == 'view_stats' and role.view_stats) or
        (permission == 'view_logs' and role.view_logs)):
        return True
    flash("You don't have permission to do that", "error")
    return False


def delete_entry_with_id(table, entry_id):
    """ Delete SQL database entry with specific id """
    try:
        entries = table.query.filter(
            table.id == entry_id).first()
        db.session.delete(entries)
        db.session.commit()
        flash(gettext(u"%(msg)s",
                      msg=u'{action} {table} with ID: {id}'.format(
                          action=gettext(u"Delete"),
                          table=table.__tablename__,
                          id=entry_id)),
              "success")
        return 1
    except sqlalchemy.orm.exc.NoResultFound:
        flash(gettext(u"%(err)s",
                      err=gettext(u"Entry with ID %(id)s not found",
                                  id=entry_id)),
              "error")
        flash(gettext(u"%(msg)s",
                      msg=u'{action} {id}: {err}'.format(
                          action=gettext(u"Delete"),
                          id=entry_id,
                          err=gettext(u"Entry with ID %(id)s not found",
                                      id=entry_id))),
              "success")
        return 0


def flash_form_errors(form):
    """ Flashes form errors for easier display """
    for field, errors in form.errors.items():
        for error in errors:
            flash(gettext(u"Error in the %(field)s field - %(err)s",
                          field=getattr(form, field).label.text,
                          err=error),
                  "error")


def flash_success_errors(error, action, redirect_url):
    if error:
        for each_error in error:
            flash(gettext(u"%(msg)s",
                          msg=u'{action}: {err}'.format(
                              action=action,
                              err=each_error)),
                  "error")
        return redirect(redirect_url)
    else:
        flash(gettext(u"%(msg)s",
                      msg=action),
              "success")


def add_display_order(display_order, device_id):
    """ Add integer ID to list of string IDs """
    if display_order:
        display_order.append(device_id)
        display_order = [str(i) for i in display_order]
        return ','.join(display_order)
    return str(device_id)


def reorder(display_order, device_id, direction):
    if direction == 'up':
        status, reord_list = reorder_list(
            display_order,
            device_id,
            'up')
    elif direction == 'down':
        status, reord_list = reorder_list(
            display_order,
            device_id,
            'down')
    else:
        status = "Fail"
        reord_list = "unrecognized command"
    return status, reord_list


def reorder_list(modified_list, item, direction):
    """ Reorder entry in a comma-separated list either up or down """
    from_position = modified_list.index(item)
    if direction == "up":
        if from_position == 0:
            return 'error', gettext(u'Cannot move above the first item in the list')
        to_position = from_position - 1
    elif direction == 'down':
        if from_position == len(modified_list) - 1:
            return 'error', gettext(u'Cannot move below the last item in the list')
        to_position = from_position + 1
    else:
        return 'error', []
    modified_list.insert(to_position, modified_list.pop(from_position))
    return 'success', modified_list


def test_sql():
    try:
        num_entries = 1000000
        factor_info = 25000
        PID.query.delete()
        db.session.commit()
        logger.error("Starting SQL uuid generation test: "
                     "{n} entries...".format(n=num_entries))
        before_count = PID.query.count()
        run_times = []
        a = datetime.now()
        for x in range(1, num_entries + 1):
            db.session.add(PID())
            if x % factor_info == 0:
                db.session.commit()
                after_count = PID.query.count()
                b = datetime.now()
                run_times.append(float((b - a).total_seconds()))
                logger.error("Run Time: {time:.2f} sec, "
                             "New entries: {new}, "
                             "Total entries: {tot}".format(
                                time=run_times[-1],
                                new=after_count - before_count,
                                tot=PID.query.count()))
                before_count = PID.query.count()
                a = datetime.now()
        avg_run_time = sum(run_times) / float(len(run_times))
        logger.error("Finished. Total: {tot} entries. "
                     "Averages: {avg:.2f} sec, "
                     "{epm:.2f} entries/min".format(
                        tot=PID.query.count(),
                        avg=avg_run_time,
                        epm=(factor_info / avg_run_time) * 60.0))
    except Exception as msg:
        logger.error("Error creating entries: {err}".format(err=msg))
