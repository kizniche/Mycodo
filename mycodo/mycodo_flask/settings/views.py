# coding=utf-8
""" collection of Page endpoints """
import logging

from flask.blueprints import Blueprint
from flask import current_app
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import session

from databases.mycodo_db.models import CameraStill
from databases.mycodo_db.models import Misc
from databases.mycodo_db.models import SMTP
from databases.users_db.models import Users

from mycodo import flaskforms
from mycodo import flaskutils
from mycodo.mycodo_flask.general_routes import (before_blueprint_request,
                                                inject_mycodo_version,
                                                logged_in)


logger = logging.getLogger('mycodo.mycodo_flask.settings')

blueprint = Blueprint('settings_routes', __name__, static_folder='../static', template_folder='../templates')
blueprint.before_request(before_blueprint_request)  # check if admin was created


@blueprint.context_processor
def inject_dictionary():
    return inject_mycodo_version()


@blueprint.route('/settings/alerts', methods=('GET', 'POST'))
def settings_alerts():
    """ Display alert settings """
    if not logged_in():
        return redirect('/')

    if session['user_group'] == 'guest':
        flash("Guests are not permitted to view alert settings.", "error")
        return redirect('/settings')

    smtp = flaskutils.db_retrieve_table(current_app.config['MYCODO_DB_PATH'], SMTP)
    formEmailAlert = flaskforms.EmailAlert()

    if request.method == 'POST':
        form_name = request.form['form-name']
        # Update smtp settings table in mycodo SQL database
        if form_name == 'EmailAlert':
            flaskutils.settings_alert_mod(formEmailAlert)
        return redirect('/settings/alerts')

    return render_template('settings/alerts.html',
                           smtp=smtp,
                           formEmailAlert=formEmailAlert)


@blueprint.route('/settings/camera', methods=('GET', 'POST'))
def settings_camera():
    """ Display camera settings """
    if not logged_in():
        return redirect('/')

    camera = flaskutils.db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], CameraStill, first=True)
    formSettingsCamera = flaskforms.SettingsCamera()

    if request.method == 'POST':
        form_name = request.form['form-name']
        if form_name == 'Camera':
            flaskutils.settings_camera_mod(formSettingsCamera)
        return redirect('/settings/camera')

    return render_template('settings/camera.html',
                           camera=camera,
                           formSettingsCamera=formSettingsCamera)


@blueprint.route('/settings/general', methods=('GET', 'POST'))
def settings_general():
    """ Display general settings """
    if not logged_in():
        return redirect('/')

    misc = flaskutils.db_retrieve_table(current_app.config['MYCODO_DB_PATH'], Misc, first=True)
    formSettingsGeneral = flaskforms.SettingsGeneral()

    if request.method == 'POST':
        form_name = request.form['form-name']
        if form_name == 'General':
            flaskutils.settings_general_mod(formSettingsGeneral)
        return redirect('/settings/general')

    return render_template('settings/general.html',
                           misc=misc,
                           formSettingsGeneral=formSettingsGeneral)


@blueprint.route('/settings/users', methods=('GET', 'POST'))
def settings_users():
    """ Display user settings """
    if not logged_in():
        return redirect('/')

    if session['user_group'] == 'guest':
        flash("Guests are not permitted to view user settings.", "error")
        return redirect('/')

    users = flaskutils.db_retrieve_table(current_app.config['USER_DB_PATH'], Users)
    formAddUser = flaskforms.AddUser()
    formModUser = flaskforms.ModUser()
    formDelUser = flaskforms.DelUser()

    if request.method == 'POST':
        form_name = request.form['form-name']
        if form_name == 'addUser':
            flaskutils.user_add(formAddUser)
        elif form_name == 'delUser':
            if flaskutils.user_del(formDelUser) == 'logout':
                return redirect('/logout')
        elif form_name == 'modUser':
            if flaskutils.user_mod(formModUser) == 'logout':
                return redirect('/logout')
        return redirect('/settings/users')

    return render_template('settings/users.html',
                           users=users,
                           formAddUser=formAddUser,
                           formModUser=formModUser,
                           formDelUser=formDelUser)
