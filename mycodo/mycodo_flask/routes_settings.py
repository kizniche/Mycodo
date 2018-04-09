# coding=utf-8
""" collection of Page endpoints """
import logging

import flask_login
import operator
import os
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask.blueprints import Blueprint

from mycodo.config import CAMERA_LIBRARIES
from mycodo.config import LANGUAGES
from mycodo.config import THEMES
from mycodo.databases.models import Camera
from mycodo.databases.models import Misc
from mycodo.databases.models import Output
from mycodo.databases.models import Role
from mycodo.databases.models import SMTP
from mycodo.databases.models import User
from mycodo.mycodo_flask.forms import forms_settings
from mycodo.mycodo_flask.routes_static import inject_variables
from mycodo.mycodo_flask.utils import utils_general
from mycodo.mycodo_flask.utils import utils_settings
from mycodo.utils.system_pi import cmd_output

logger = logging.getLogger('mycodo.mycodo_flask.settings')

blueprint = Blueprint('routes_settings',
                      __name__,
                      static_folder='../static',
                      template_folder='../templates')


@blueprint.context_processor
@flask_login.login_required
def inject_dictionary():
    return inject_variables()


@blueprint.route('/settings/alerts', methods=('GET', 'POST'))
@flask_login.login_required
def settings_alerts():
    """ Display alert settings """
    if not utils_general.user_has_permission('view_settings'):
        return redirect(url_for('routes_general.home'))

    smtp = SMTP.query.first()
    form_email_alert = forms_settings.SettingsEmail()

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_settings'):
            return redirect(url_for('routes_general.home'))

        form_name = request.form['form-name']
        if form_name == 'EmailAlert':
            utils_settings.settings_alert_mod(form_email_alert)
        return redirect(url_for('routes_settings.settings_alerts'))

    return render_template('settings/alerts.html',
                           smtp=smtp,
                           form_email_alert=form_email_alert)


@blueprint.route('/settings/camera', methods=('GET', 'POST'))
@flask_login.login_required
def settings_camera():
    """ Display camera settings """
    if not utils_general.user_has_permission('view_settings'):
        return redirect(url_for('routes_general.home'))

    form_camera = forms_settings.SettingsCamera()

    camera = Camera.query.all()
    output = Output.query.all()

    pi_camera_enabled = False
    try:
        if 'start_x=1' in open('/boot/config.txt').read():
            pi_camera_enabled = True
    except IOError as e:
        logger.error("Camera IOError raised in '/settings/camera' endpoint: "
                     "{err}".format(err=e))

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_settings'):
            return redirect(url_for('routes_general.home'))

        if form_camera.camera_add.data:
            utils_settings.camera_add(form_camera)
        elif form_camera.camera_mod.data:
            utils_settings.camera_mod(form_camera)
        elif form_camera.camera_del.data:
            utils_settings.camera_del(form_camera)
        return redirect(url_for('routes_settings.settings_camera'))

    return render_template('settings/camera.html',
                           camera=camera,
                           camera_libraries=CAMERA_LIBRARIES,
                           form_camera=form_camera,
                           pi_camera_enabled=pi_camera_enabled,
                           output=output)


@blueprint.route('/settings/general', methods=('GET', 'POST'))
@flask_login.login_required
def settings_general():
    """ Display general settings """
    if not utils_general.user_has_permission('view_settings'):
        return redirect(url_for('routes_general.home'))

    misc = Misc.query.first()
    form_settings_general = forms_settings.SettingsGeneral()

    languages_sorted = sorted(LANGUAGES.items(), key=operator.itemgetter(1))

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_settings'):
            return redirect(url_for('routes_general.home'))

        form_name = request.form['form-name']
        if form_name == 'General':
            utils_settings.settings_general_mod(form_settings_general)
        return redirect(url_for('routes_settings.settings_general'))

    return render_template('settings/general.html',
                           misc=misc,
                           languages=languages_sorted,
                           form_settings_general=form_settings_general)


@blueprint.route('/settings/users', methods=('GET', 'POST'))
@flask_login.login_required
def settings_users():
    """ Display user settings """
    if not utils_general.user_has_permission('view_settings'):
        return redirect(url_for('routes_general.home'))

    users = User.query.all()
    user_roles = Role.query.all()
    form_add_user = forms_settings.UserAdd()
    form_mod_user = forms_settings.UserMod()
    form_user_roles = forms_settings.UserRoles()

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_users'):
            return redirect(url_for('routes_general.home'))

        if form_add_user.add_user.data:
            utils_settings.user_add(form_add_user)
        elif form_mod_user.delete.data:
            if utils_settings.user_del(form_mod_user) == 'logout':
                return redirect('/logout')
        elif form_mod_user.save.data:
            if utils_settings.user_mod(form_mod_user) == 'logout':
                return redirect('/logout')
        elif (form_user_roles.add_role.data or
                form_user_roles.save_role.data or
                form_user_roles.delete_role.data):
            utils_settings.user_roles(form_user_roles)
        return redirect(url_for('routes_settings.settings_users'))

    return render_template('settings/users.html',
                           themes=THEMES,
                           users=users,
                           user_roles=user_roles,
                           form_add_user=form_add_user,
                           form_mod_user=form_mod_user,
                           form_user_roles=form_user_roles)

@blueprint.route('/settings/pi', methods=('GET', 'POST'))
@flask_login.login_required
def settings_pi():
    """ Display general settings """
    if not utils_general.user_has_permission('view_settings'):
        return redirect(url_for('routes_general.home'))

    misc = Misc.query.first()
    form_settings_pi = forms_settings.SettingsPi()

    pi_settings = get_raspi_config_settings()

    # Determine what state pigpiod is currently in
    pigpiod_sample_rate = ''
    if os.path.exists('/etc/systemd/system/pigpiod_uninstalled.service'):
        pigpiod_sample_rate = 'uninstalled'
    elif os.path.exists('/etc/systemd/system/pigpiod_disabled.service'):
        pigpiod_sample_rate = 'disabled'
    elif os.path.exists('/etc/systemd/system/pigpiod_low.service'):
        pigpiod_sample_rate = 'low'
    elif os.path.exists('/etc/systemd/system/pigpiod_high.service'):
        pigpiod_sample_rate = 'high'
    elif os.path.exists('/etc/systemd/system/pigpiod.service'):
        pigpiod_sample_rate = 'low'

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_settings'):
            return redirect(url_for('routes_general.home'))

        form_name = request.form['form-name']
        if form_name == 'Pi':
            utils_settings.settings_pi_mod(form_settings_pi)
        return redirect(url_for('routes_settings.settings_pi'))

    return render_template('settings/pi.html',
                           misc=misc,
                           pi_settings=pi_settings,
                           pigpiod_sample_rate=pigpiod_sample_rate,
                           form_settings_pi=form_settings_pi)

def get_raspi_config_settings():
    settings = {}
    i2c_status, _, _ = cmd_output("raspi-config nonint get_i2c")
    settings['i2c_enabled'] = not bool(int(i2c_status))
    ssh_status, _, _ = cmd_output("raspi-config nonint get_ssh")
    settings['ssh_enabled'] = not bool(int(ssh_status))
    cam_status, _, _ = cmd_output("raspi-config nonint get_camera")
    settings['pi_camera_enabled'] = not bool(int(cam_status))
    one_wire_status, _, _ = cmd_output("raspi-config nonint get_onewire")
    settings['one_wire_enabled'] = not bool(int(one_wire_status))
    serial_status, _, _ = cmd_output("raspi-config nonint get_serial")
    settings['serial_enabled'] = not bool(int(serial_status))
    spi_status, _, _ = cmd_output("raspi-config nonint get_spi")
    settings['spi_enabled'] = not bool(int(spi_status))
    hostname_out, _, _ = cmd_output("raspi-config nonint get_hostname")
    settings['hostname'] = hostname_out.decode("utf-8")
    return settings
