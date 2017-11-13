# -*- coding: utf-8 -*-
import logging
import functools
import gzip
import sqlalchemy
import flask_login
from collections import OrderedDict
from datetime import datetime
from cStringIO import StringIO as IO

from flask import after_this_request
from flask import flash
from flask import redirect
from flask import request
from flask import url_for

from mycodo.mycodo_flask.extensions import db
from flask_babel import gettext

from mycodo.mycodo_client import DaemonControl

from mycodo.databases.models import LCD
from mycodo.databases.models import PID
from mycodo.databases.models import Sensor
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
    :param controller_type: The controller type (LCD, PID, Sensor, Timer)
    :type controller_type: str
    :param controller_id: Controller with ID to activate or deactivate
    :type controller_id: str
    """
    if not user_has_permission('edit_controllers'):
        return redirect(url_for('general_routes.home'))

    activated = bool(controller_action == 'activate')

    translated_names = {
        "LCD": gettext(u"LCD"),
        "PID": gettext(u"PID"),
        "Sensor": gettext(u"Sensor"),
        "Timer": gettext(u"Timer")
    }

    mod_controller = None
    if controller_type == 'LCD':
        mod_controller = LCD.query.filter(
            LCD.id == int(controller_id)).first()
    elif controller_type == 'PID':
        mod_controller = PID.query.filter(
            PID.id == int(controller_id)).first()
    elif controller_type == 'Sensor':
        mod_controller = Sensor.query.filter(
            Sensor.id == int(controller_id)).first()
    elif controller_type == 'Timer':
        mod_controller = Timer.query.filter(
            Timer.id == int(controller_id)).first()

    if mod_controller is None:
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

def choices_inputs(sensor):
    """ populate form multi-select choices from Input entries """
    choices = OrderedDict()
    for each_sensor in sensor:
        if each_sensor.device == 'LinuxCommand':
            value = '{id},{meas}'.format(
                id=each_sensor.unique_id,
                meas=each_sensor.cmd_measurement)
            display = u'[{id:02d}] {name} ({meas})'.format(
                id=each_sensor.id,
                name=each_sensor.name,
                meas=each_sensor.cmd_measurement)
            choices.update({value: display})
        else:
            for each_measurement in MEASUREMENTS[each_sensor.device]:
                value = '{id},{meas}'.format(
                    id=each_sensor.unique_id,
                    meas=each_measurement)
                display = u'[{id:02d}] {name} ({meas})'.format(
                    id=each_sensor.id,
                    name=each_sensor.name,
                    meas=MEASUREMENT_UNITS[each_measurement]['name'])
                choices.update({value: display})
            # Display custom converted units for ADCs
            if each_sensor.device in ['ADS1x15', 'MCP342x']:
                value = '{id},{meas}'.format(
                    id=each_sensor.unique_id,
                    meas=each_sensor.adc_measure)
                display = u'[{id:02d}] {name} ({meas})'.format(
                    id=each_sensor.id,
                    name=each_sensor.name,
                    meas=each_sensor.adc_measure)
                choices.update({value: display})
    return choices


def choices_outputs(output):
    """ populate form multi-select choices from Output entries """
    choices = OrderedDict()
    for each_output in output:
        if each_output.relay_type != 'pwm':
            value = '{id},duration_sec'.format(id=each_output.unique_id)
            display = u'[{id:02d}] {name} (Duration)'.format(
                id=each_output.id, name=each_output.name)
            choices.update({value: display})
        elif each_output.relay_type == 'pwm':
            value = '{id},duty_cycle'.format(id=each_output.unique_id)
            display = u'[{id:02d}] {name} (Duty Cycle)'.format(
                id=each_output.id, name=each_output.name)
            choices.update({value: display})
    return choices


def choices_pids(pid):
    """ populate form multi-select choices from PID entries """
    choices = OrderedDict()
    for each_pid in pid:
        value = '{id},setpoint'.format(id=each_pid.unique_id)
        display = u'[{id:02d}] {name} (Setpoint)'.format(
            id=each_pid.id, name=each_pid.name)
        choices.update({value: display})
        value = '{id},pid_output'.format(id=each_pid.unique_id)
        display = u'[{id:02d}] {name} (Output Duration)'.format(
            id=each_pid.id, name=each_pid.name)
        choices.update({value: display})
        value = '{id},duty_cycle'.format(id=each_pid.unique_id)
        display = u'[{id:02d}] {name} (Output Duty Cycle)'.format(
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
    if ((permission == 'edit_settings' and user.roles.edit_settings) or
        (permission == 'edit_controllers' and user.roles.edit_controllers) or
        (permission == 'edit_users' and user.roles.edit_users) or
        (permission == 'view_settings' and user.roles.view_settings) or
        (permission == 'view_camera' and user.roles.view_camera) or
        (permission == 'view_stats' and user.roles.view_stats) or
        (permission == 'view_logs' and user.roles.view_logs)):
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


def gzipped(f):
    """
    Allows gzipping the response of any view.
    Just add '@gzipped' after the '@app'.
    Used mainly for sending large amounts of data for graphs.
    """
    @functools.wraps(f)
    def view_func(*args, **kwargs):
        @after_this_request
        def zipper(response):
            accept_encoding = request.headers.get('Accept-Encoding', '')

            if 'gzip' not in accept_encoding.lower():
                return response

            response.direct_passthrough = False

            if (response.status_code < 200 or
                    response.status_code >= 300 or
                    'Content-Encoding' in response.headers):
                return response
            gzip_buffer = IO()
            gzip_file = gzip.GzipFile(mode='wb',
                                      fileobj=gzip_buffer)

            gzip_file.write(response.data)
            gzip_file.close()

            response.data = gzip_buffer.getvalue()
            response.headers['Content-Encoding'] = 'gzip'
            response.headers['Vary'] = 'Accept-Encoding'
            response.headers['Content-Length'] = len(response.data)

            return response

        return f(*args, **kwargs)

    return view_func


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
