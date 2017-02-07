# coding=utf-8
""" collection of Page endpoints """
import logging
import operator

from flask import (
    current_app,
    redirect,
    render_template,
    request,
    session,
    url_for
)
from flask.blueprints import Blueprint

# Classes
from mycodo.databases.mycodo_db.models import (
    CameraStill,
    Misc,
    SMTP
)
from mycodo.databases.users_db.models import Users

# Functions
from mycodo import flaskforms
from mycodo import flaskutils
from mycodo.utils.database import db_retrieve_table

# Config
from config import LANGUAGES

from mycodo.mycodo_flask.general_routes import (
    before_blueprint_request,
    inject_mycodo_version,
    logged_in
)

logger = logging.getLogger('mycodo.mycodo_flask.settings')

blueprint = Blueprint('settings_routes',
                      __name__,
                      static_folder='../static',
                      template_folder='../templates')
blueprint.before_request(before_blueprint_request)  # check if admin was created


@blueprint.context_processor
def inject_dictionary():
    return inject_mycodo_version()


@blueprint.route('/settings/alerts', methods=('GET', 'POST'))
def settings_alerts():
    """ Display alert settings """
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    if session['user_group'] == 'guest':
        flaskutils.deny_guest_user()
        return redirect(url_for('settings_routes.settings_general'))

    smtp = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], SMTP, entry='first')
    form_email_alert = flaskforms.EmailAlert()

    if request.method == 'POST':
        form_name = request.form['form-name']
        # Update smtp settings table in mycodo SQL database
        if form_name == 'EmailAlert':
            flaskutils.settings_alert_mod(form_email_alert)
        return redirect(url_for('settings_routes.settings_alerts'))

    return render_template('settings/alerts.html',
                           smtp=smtp,
                           form_email_alert=form_email_alert)


@blueprint.route('/settings/camera', methods=('GET', 'POST'))
def settings_camera():
    """ Display camera settings """
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    camera = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], CameraStill, entry='first')
    form_settings_camera = flaskforms.SettingsCamera()

    if request.method == 'POST':
        form_name = request.form['form-name']
        if form_name == 'Camera':
            flaskutils.settings_camera_mod(form_settings_camera)
        return redirect(url_for('settings_routes.settings_camera'))

    return render_template('settings/camera.html',
                           camera=camera,
                           form_settings_camera=form_settings_camera)


@blueprint.route('/settings/general', methods=('GET', 'POST'))
def settings_general():
    """ Display general settings """
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    misc = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], Misc, entry='first')
    form_settings_general = flaskforms.SettingsGeneral()

    languages_sorted = sorted(LANGUAGES.items(), key=operator.itemgetter(1))

    if request.method == 'POST':
        form_name = request.form['form-name']
        if form_name == 'General':
            flaskutils.settings_general_mod(form_settings_general)
        return redirect(url_for('settings_routes.settings_general'))

    return render_template('settings/general.html',
                           misc=misc,
                           languages=languages_sorted,
                           form_settings_general=form_settings_general)


@blueprint.route('/settings/users', methods=('GET', 'POST'))
def settings_users():
    """ Display user settings """
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    if session['user_group'] == 'guest':
        flaskutils.deny_guest_user()
        return redirect(url_for('settings_routes.settings_general'))

    users = db_retrieve_table(
        current_app.config['USER_DB_PATH'], Users, entry='all')
    form_add_user = flaskforms.AddUser()
    form_mod_user = flaskforms.ModUser()
    form_del_user = flaskforms.DelUser()

    if request.method == 'POST':
        form_name = request.form['form-name']
        if form_name == 'addUser':
            flaskutils.user_add(form_add_user)
        elif form_name == 'delUser':
            if flaskutils.user_del(form_del_user) == 'logout':
                return redirect('/logout')
        elif form_name == 'modUser':
            if flaskutils.user_mod(form_mod_user) == 'logout':
                return redirect('/logout')
        return redirect(url_for('settings_routes.settings_users'))

    return render_template('settings/users.html',
                           users=users,
                           form_add_user=form_add_user,
                           form_mod_user=form_mod_user,
                           form_del_user=form_del_user)
