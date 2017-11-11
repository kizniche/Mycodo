# -*- coding: utf-8 -*-
import logging
import bcrypt
import os
import sqlalchemy
import flask_login

from flask import flash
from flask import redirect
from flask import url_for

from mycodo.mycodo_flask.extensions import db
from flask_babel import gettext

from mycodo.mycodo_client import DaemonControl

from mycodo.databases.models import Camera
from mycodo.databases.models import Misc
from mycodo.databases.models import Role
from mycodo.databases.models import SMTP
from mycodo.databases.models import User
from mycodo.utils.database import db_retrieve_table
from mycodo.utils.utils import test_username
from mycodo.utils.utils import test_password
from mycodo.utils.send_data import send_email

from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.mycodo_flask.utils.utils_general import flash_form_errors
from mycodo.mycodo_flask.utils.utils_general import flash_success_errors

from mycodo.config import INSTALL_DIRECTORY

logger = logging.getLogger(__name__)


#
# User manipulation
#

def user_roles(form):
    action = None
    if form.add_role.data:
        action = gettext(u"Add")
    elif form.save_role.data:
        action = gettext(u"Modify")
    elif form.delete_role.data:
        action = gettext(u"Delete")

    action = u'{action} {controller}'.format(
        action=action,
        controller=gettext(u"User Role"))
    error = []

    if not error:
        if form.add_role.data:
            new_role = Role()
            new_role.name = form.name.data
            new_role.view_logs = form.view_logs.data
            new_role.view_camera = form.view_camera.data
            new_role.view_stats = form.view_stats.data
            new_role.view_settings = form.view_settings.data
            new_role.edit_users = form.edit_users.data
            new_role.edit_settings = form.edit_settings.data
            new_role.edit_controllers = form.edit_controllers.data
            try:
                new_role.save()
            except sqlalchemy.exc.OperationalError as except_msg:
                error.append(except_msg)
            except sqlalchemy.exc.IntegrityError as except_msg:
                error.append(except_msg)
        elif form.save_role.data:
            mod_role = Role.query.filter(Role.id == form.role_id.data).first()
            mod_role.view_logs = form.view_logs.data
            mod_role.view_camera = form.view_camera.data
            mod_role.view_stats = form.view_stats.data
            mod_role.view_settings = form.view_settings.data
            mod_role.edit_users = form.edit_users.data
            mod_role.edit_settings = form.edit_settings.data
            mod_role.edit_controllers = form.edit_controllers.data
            db.session.commit()
        elif form.delete_role.data:
            if User().query.filter(User.role == form.role_id.data).count():
                error.append(
                    "Cannot delete role if it is assigned to a user. "
                    "Change the user to another role and try again.")
            else:
                delete_entry_with_id(Role,
                                     form.role_id.data)
    flash_success_errors(error, action, url_for('settings_routes.settings_users'))


def user_add(form):
    action = u'{action} {controller}'.format(
        action=gettext(u"Add"),
        controller=gettext(u"User"))
    error = []

    if form.validate():
        new_user = User()
        if not test_username(form.user_name.data):
            error.append(gettext(
                u"Invalid user name. Must be between 2 and 64 characters "
                u"and only contain letters and numbers."))

        if User.query.filter_by(email=form.email.data).count():
            error.append(gettext(
                u"Another user already has that email address."))

        if not test_password(form.password_new.data):
            error.append(gettext(
                u"Invalid password. Must be between 6 and 64 characters "
                u"and only contain letters, numbers, and symbols."))

        if form.password_new.data != form.password_repeat.data:
            error.append(gettext(u"Passwords do not match. Please try again."))

        if not error:
            new_user.name = form.user_name.data
            new_user.email = form.email.data
            new_user.set_password(form.password_new.data)
            role = Role.query.filter(
                Role.name == form.addRole.data).first().id
            new_user.role = role
            new_user.theme = 'slate'
            try:
                new_user.save()
            except sqlalchemy.exc.OperationalError as except_msg:
                error.append(except_msg)
            except sqlalchemy.exc.IntegrityError as except_msg:
                error.append(except_msg)

        flash_success_errors(error, action, url_for('settings_routes.settings_users'))
    else:
        flash_form_errors(form)


def user_mod(form):
    action = u'{action} {controller}'.format(
        action=gettext(u"Modify"),
        controller=gettext(u"User"))
    error = []

    try:
        mod_user = User.query.filter(
            User.id == form.user_id.data).first()
        mod_user.email = form.email.data
        # Only change the password if it's entered in the form
        logout_user = False
        if form.password_new.data != '':
            if not test_password(form.password_new.data):
                error.append(gettext(u"Invalid password"))
            if form.password_new.data == form.password_repeat.data:
                mod_user.password_hash = bcrypt.hashpw(
                    form.password_new.data.encode('utf-8'),
                    bcrypt.gensalt())
                if flask_login.current_user.id == form.user_id.data:
                    logout_user = True
            else:
                error.append(gettext(u"Passwords do not match. Please try again."))

        if not error:
            role = Role.query.filter(
                Role.name == form.role.data).first().id
            mod_user.role = role
            mod_user.theme = form.theme.data
            db.session.commit()
            if logout_user:
                return 'logout'
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('settings_routes.settings_users'))


def delete_user(user_id):
    """ Delete user from SQL database """
    try:
        user = User.query.filter(
            User.id == user_id).first()
        user_name = user.name
        user.delete()
        flash(gettext(u"%(msg)s",
                      msg=u'{action} {user}'.format(
                          action=gettext(u"Delete"),
                          user=user_name)),
              "success")
        return 1
    except sqlalchemy.orm.exc.NoResultFound:
        flash(gettext(u"%(err)s",
                      err=gettext(u"User not found")),
              "error")
        return 0


def user_del(form):
    """ Form request to delete a user """
    user_name = None
    try:
        if form.validate():
            user_name = User.query.filter(User.id == form.user_id.data).first().name
            delete_user(form.user_id.data)
            if form.user_id.data == flask_login.current_user.id:
                return 'logout'
        else:
            flash_form_errors(form)
    except Exception as except_msg:
        flash(gettext(u"Error: %(msg)s",
                      msg=u'{action} {user}: {err}'.format(
                          action=gettext(u"Delete"),
                          user=user_name,
                          err=except_msg)),
              "error")


#
# Settings modifications
#

def settings_general_mod(form):
    """ Modify General settings """
    action = u'{action} {controller}'.format(
        action=gettext(u"Modify"),
        controller=gettext(u"General Settings"))
    error = []

    if form.validate():
        if (form.relay_usage_report_span.data == 'monthly' and
                not 0 < form.relay_usage_report_day.data < 29):
            error.append("Day Options: Daily: 1-7 (1=Monday), Monthly: 1-28")
        elif (form.relay_usage_report_span.data == 'weekly' and
                not 0 < form.relay_usage_report_day.data < 8):
            error.append("Day Options: Daily: 1-7 (1=Monday), Monthly: 1-28")

        if not error:
            try:
                mod_misc = Misc.query.first()
                force_https = mod_misc.force_https
                mod_misc.language = form.language.data
                mod_misc.force_https = form.force_https.data
                mod_misc.hide_alert_success = form.hide_success.data
                mod_misc.hide_alert_info = form.hide_info.data
                mod_misc.hide_alert_warning = form.hide_warning.data
                mod_misc.hide_tooltips = form.hide_tooltips.data
                mod_misc.max_amps = form.max_amps.data
                mod_misc.relay_usage_volts = form.relay_stats_volts.data
                mod_misc.relay_usage_cost = form.relay_stats_cost.data
                mod_misc.relay_usage_currency = form.relay_stats_currency.data
                mod_misc.relay_usage_dayofmonth = form.relay_stats_day_month.data
                mod_misc.relay_usage_report_gen = form.relay_usage_report_gen.data
                mod_misc.relay_usage_report_span = form.relay_usage_report_span.data
                mod_misc.relay_usage_report_day = form.relay_usage_report_day.data
                mod_misc.relay_usage_report_hour = form.relay_usage_report_hour.data
                mod_misc.stats_opt_out = form.stats_opt_out.data
                db.session.commit()
                control = DaemonControl()
                control.refresh_daemon_misc_settings()

                if force_https != form.force_https.data:
                    # Force HTTPS option changed.
                    # Reload web server with new settings.
                    wsgi_file = INSTALL_DIRECTORY + '/mycodo_flask.wsgi'
                    with open(wsgi_file, 'a'):
                        os.utime(wsgi_file, None)

            except Exception as except_msg:
                error.append(except_msg)

        flash_success_errors(error, action, url_for('settings_routes.settings_general'))
    else:
        flash_form_errors(form)


def settings_alert_mod(form_mod_alert):
    """ Modify Alert settings """
    action = u'{action} {controller}'.format(
        action=gettext(u"Modify"),
        controller=gettext(u"Alert Settings"))
    error = []

    try:
        if form_mod_alert.validate():
            mod_smtp = SMTP.query.one()
            if form_mod_alert.send_test.data:
                send_email(
                    mod_smtp.host, mod_smtp.ssl, mod_smtp.port,
                    mod_smtp.user, mod_smtp.passw, mod_smtp.email_from,
                    form_mod_alert.send_test_to_email.data,
                    u"This is a test email from Mycodo")
                flash(gettext(u"Test email sent to %(recip)s. Check your "
                              u"inbox to see if it was successful.",
                              recip=form_mod_alert.send_test_to_email.data),
                      "success")
                return redirect(url_for('settings_routes.settings_alerts'))
            else:
                mod_smtp.host = form_mod_alert.smtp_host.data
                mod_smtp.port = form_mod_alert.smtp_port.data
                mod_smtp.ssl = form_mod_alert.smtp_ssl.data
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

    flash_success_errors(error, action, url_for('settings_routes.settings_alerts'))


def camera_add(form_camera):
    action = u'{action} {controller}'.format(
        action=gettext(u"Add"),
        controller=gettext(u"Camera"))
    error = []

    if form_camera.validate():
        new_camera = Camera()
        if Camera.query.filter(Camera.name == form_camera.name.data).count():
            flash("You must choose a unique name", "error")
            return redirect(url_for('settings_routes.settings_camera'))
        new_camera.name = form_camera.name.data
        new_camera.library = form_camera.library.data
        if form_camera.library.data == 'opencv':
            new_camera.brightness = 0.75
            new_camera.contrast = 0.2
            new_camera.exposure = 0.0
            new_camera.gain = 0.0
            new_camera.hue = 0.0
            new_camera.saturation = 0.0
            new_camera.white_balance = 0.0
        elif form_camera.library.data == 'picamera':
            new_camera.brightness = 50
            new_camera.contrast = 0.0
            new_camera.exposure = 0.0
            new_camera.saturation = 0.0
        if not error:
            try:
                new_camera.save()
            except sqlalchemy.exc.OperationalError as except_msg:
                error.append(except_msg)
            except sqlalchemy.exc.IntegrityError  as except_msg:
                error.append(except_msg)

        flash_success_errors(error, action, url_for('settings_routes.settings_camera'))
    else:
        flash_form_errors(form_camera)


def camera_mod(form_camera):
    action = u'{action} {controller}'.format(
        action=gettext(u"Modify"),
        controller=gettext(u"Camera"))
    error = []

    try:
        if (Camera.query
                .filter(Camera.id != form_camera.camera_id.data)
                .filter(Camera.name == form_camera.name.data).count()):
            flash("You must choose a unique name", "error")
            return redirect(url_for('settings_routes.settings_camera'))
        if 0 > form_camera.rotation.data > 360:
            flash("Rotation must be between 0 and 360 degrees", "error")
            return redirect(url_for('settings_routes.settings_camera'))

        mod_camera = Camera.query.filter(
            Camera.id == form_camera.camera_id.data).first()
        mod_camera.name = form_camera.name.data

        if mod_camera.library == 'opencv':
            mod_camera.opencv_device = form_camera.opencv_device.data
            mod_camera.hflip = form_camera.hflip.data
            mod_camera.vflip = form_camera.vflip.data
            mod_camera.rotation = form_camera.rotation.data
            mod_camera.height = form_camera.height.data
            mod_camera.width = form_camera.width.data
            mod_camera.brightness = form_camera.brightness.data
            mod_camera.contrast = form_camera.contrast.data
            mod_camera.exposure = form_camera.exposure.data
            mod_camera.gain = form_camera.gain.data
            mod_camera.hue = form_camera.hue.data
            mod_camera.saturation = form_camera.saturation.data
            mod_camera.white_balance = form_camera.white_balance.data
        elif mod_camera.library == 'picamera':
            mod_camera.hflip = form_camera.hflip.data
            mod_camera.vflip = form_camera.vflip.data
            mod_camera.rotation = form_camera.rotation.data
            mod_camera.height = form_camera.height.data
            mod_camera.width = form_camera.width.data
            mod_camera.brightness = form_camera.brightness.data
            mod_camera.contrast = form_camera.contrast.data
            mod_camera.exposure = form_camera.exposure.data
            mod_camera.saturation = form_camera.saturation.data
        else:
            error.append("Unknown camera library")

        if form_camera.relay_id.data:
            mod_camera.relay_id = form_camera.relay_id.data
        else:
            mod_camera.relay_id = None
        mod_camera.cmd_pre_camera = form_camera.cmd_pre_camera.data
        mod_camera.cmd_post_camera = form_camera.cmd_post_camera.data

        if not error:
            db.session.commit()
            control = DaemonControl()
            control.refresh_daemon_camera_settings()
    except Exception as except_msg:
        logger.exception(1)
        error.append(except_msg)

    flash_success_errors(error, action, url_for('settings_routes.settings_camera'))


def camera_del(form_camera):
    action = u'{action} {controller}'.format(
        action=gettext(u"Delete"),
        controller=gettext(u"Camera"))
    error = []

    camera = db_retrieve_table(
        Camera, device_id=form_camera.camera_id.data)
    if camera.timelapse_started:
        error.append("Cannot delete camera if a time-lapse is currently "
                     "using it. Stop the time-lapse and try again.")

    if not error:
        try:
            delete_entry_with_id(
                Camera, int(form_camera.camera_id.data))
        except Exception as except_msg:
            error.append(except_msg)

    flash_success_errors(error, action, url_for('settings_routes.settings_camera'))
