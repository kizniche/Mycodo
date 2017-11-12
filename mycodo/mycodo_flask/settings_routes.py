# coding=utf-8
""" collection of Page endpoints """
import logging
import operator
import flask_login

from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask.blueprints import Blueprint

from mycodo.databases.models import Camera
from mycodo.databases.models import Misc
from mycodo.databases.models import Relay
from mycodo.databases.models import Role
from mycodo.databases.models import SMTP
from mycodo.databases.models import User

from mycodo.mycodo_flask.forms import forms_settings
from mycodo.mycodo_flask.utils import utils_general
from mycodo.mycodo_flask.utils import utils_settings

from mycodo.devices.camera import count_cameras_opencv

from mycodo.config import CAMERA_LIBRARIES
from mycodo.config import LANGUAGES
from mycodo.config import THEMES

from mycodo.mycodo_flask.static_routes import inject_variables

logger = logging.getLogger('mycodo.mycodo_flask.settings')

blueprint = Blueprint('settings_routes',
                      __name__,
                      static_folder='../static',
                      template_folder='../templates')


@blueprint.context_processor
def inject_dictionary():
    return inject_variables()


@blueprint.route('/settings/alerts', methods=('GET', 'POST'))
@flask_login.login_required
def settings_alerts():
    """ Display alert settings """
    if not utils_general.user_has_permission('view_settings'):
        return redirect(url_for('general_routes.home'))

    smtp = SMTP.query.first()
    form_email_alert = forms_settings.SettingsEmail()

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_settings'):
            return redirect(url_for('general_routes.home'))

        form_name = request.form['form-name']
        if form_name == 'EmailAlert':
            utils_settings.settings_alert_mod(form_email_alert)
        return redirect(url_for('settings_routes.settings_alerts'))

    return render_template('settings/alerts.html',
                           smtp=smtp,
                           form_email_alert=form_email_alert)


@blueprint.route('/settings/camera', methods=('GET', 'POST'))
@flask_login.login_required
def settings_camera():
    """ Display camera settings """
    if not utils_general.user_has_permission('view_settings'):
        return redirect(url_for('general_routes.home'))

    form_camera = forms_settings.SettingsCamera()

    camera = Camera.query.all()
    relay = Relay.query.all()

    try:
        opencv_devices = count_cameras_opencv()
    except Exception:
        opencv_devices = 0

    pi_camera_enabled = False
    try:
        if 'start_x=1' in open('/boot/config.txt').read():
            pi_camera_enabled = True
    except IOError as e:
        logger.error("Camera IOError raised in '/settings/camera' endpoint: "
                     "{err}".format(err=e))

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_settings'):
            return redirect(url_for('general_routes.home'))

        if form_camera.camera_add.data:
            utils_settings.camera_add(form_camera)
        elif form_camera.camera_mod.data:
            utils_settings.camera_mod(form_camera)
        elif form_camera.camera_del.data:
            utils_settings.camera_del(form_camera)
        return redirect(url_for('settings_routes.settings_camera'))

    return render_template('settings/camera.html',
                           camera=camera,
                           camera_libraries=CAMERA_LIBRARIES,
                           form_camera=form_camera,
                           opencv_devices=opencv_devices,
                           pi_camera_enabled=pi_camera_enabled,
                           relay=relay)


@blueprint.route('/settings/general', methods=('GET', 'POST'))
@flask_login.login_required
def settings_general():
    """ Display general settings """
    if not utils_general.user_has_permission('view_settings'):
        return redirect(url_for('general_routes.home'))

    misc = Misc.query.first()
    form_settings_general = forms_settings.SettingsGeneral()

    languages_sorted = sorted(LANGUAGES.items(), key=operator.itemgetter(1))

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_settings'):
            return redirect(url_for('general_routes.home'))

        form_name = request.form['form-name']
        if form_name == 'General':
            utils_settings.settings_general_mod(form_settings_general)
        return redirect(url_for('settings_routes.settings_general'))

    return render_template('settings/general.html',
                           misc=misc,
                           languages=languages_sorted,
                           form_settings_general=form_settings_general)


@blueprint.route('/settings/users', methods=('GET', 'POST'))
@flask_login.login_required
def settings_users():
    """ Display user settings """
    if not utils_general.user_has_permission('view_settings'):
        return redirect(url_for('general_routes.home'))

    users = User.query.all()
    user_roles = Role.query.all()
    form_add_user = forms_settings.UserAdd()
    form_mod_user = forms_settings.UserMod()
    form_user_roles = forms_settings.UserRoles()

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_users'):
            return redirect(url_for('general_routes.home'))

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
        return redirect(url_for('settings_routes.settings_users'))

    return render_template('settings/users.html',
                           themes=THEMES,
                           users=users,
                           user_roles=user_roles,
                           form_add_user=form_add_user,
                           form_mod_user=form_mod_user,
                           form_user_roles=form_user_roles)
