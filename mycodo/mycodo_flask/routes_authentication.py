# coding=utf-8
"""flask views that deal with user authentication."""

import datetime
import logging
import os
import socket
import time

import flask_login
from flask import (flash, jsonify, make_response, redirect, render_template,
                   request, session, url_for)
from flask.blueprints import Blueprint
from flask_babel import gettext
from sqlalchemy import func

from mycodo.config import (INSTALL_DIRECTORY, LANGUAGES, LOGIN_ATTEMPTS,
                           LOGIN_BAN_SECONDS, LOGIN_LOG_FILE)
from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import AlembicVersion, Misc, Role, User
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.forms import forms_authentication
from mycodo.mycodo_flask.utils import utils_general
from mycodo.utils.utils import test_password, test_username

logger = logging.getLogger(__name__)

blueprint = Blueprint(
    'routes_authentication',
    __name__,
    static_folder='../static',
    template_folder='../templates'
)


@blueprint.route('/create_admin', methods=('GET', 'POST'))
def create_admin():
    if admin_exists():
        flash(gettext(
            "Cannot access admin creation form if an admin user "
            "already exists."), "error")
        return redirect(url_for('routes_general.home'))

    # If login token cookie from previous session exists, delete
    if request.cookies.get('remember_token'):
        response = clear_cookie_auth()
        return response

    form_create_admin = forms_authentication.CreateAdmin()
    form_notice = forms_authentication.InstallNotice()
    form_language = forms_authentication.LanguageSelect()

    language = None

    try:
        host = Misc.query.first().hostname_override
    except:
        host = None
    if not host:
        host = socket.gethostname()

    # Find user-selected language in Mycodo/.language
    try:
        lang_path = os.path.join(INSTALL_DIRECTORY, ".language")
        if os.path.exists(lang_path):
            with open(lang_path) as f:
                language_read = f.read().split(":")[0]
                if language and language in LANGUAGES:
                    language = language_read
    except:
        pass

    if session.get('language'):
        language = session['language']

    if request.method == 'POST':
        if form_notice.acknowledge.data:
            mod_misc = Misc.query.first()
            mod_misc.dismiss_notification = 1
            db.session.commit()
        elif form_language.language.data:
            session['language'] = form_language.language.data
            language = form_language.language.data
        elif form_create_admin.validate():
            username = form_create_admin.username.data.lower()
            error = False
            if form_create_admin.password.data != form_create_admin.password_repeat.data:
                flash(gettext("Passwords do not match. Please try again."),
                      "error")
                error = True
            if not test_username(username):
                flash(gettext(
                    "Invalid username. Must be between 3 and 64 characters "
                    "and only contain letters and numbers."),
                    "error")
                error = True
            if not test_password(form_create_admin.password.data):
                flash(gettext(
                    "Invalid password. Must be between 4 and 64 characters "
                    "and only contain letters and numbers."),
                      "error")
                error = True
            if error:
                return render_template('create_admin.html',
                                       dict_translation=TRANSLATIONS,
                                       dismiss_notification=1,
                                       form_create_admin=form_create_admin,
                                       form_language=form_language,
                                       form_notice=form_notice,
                                       host=host,
                                       language=language,
                                       languages=LANGUAGES)

            new_user = User()
            new_user.name = username
            new_user.email = form_create_admin.email.data
            new_user.set_password(form_create_admin.password.data)
            new_user.role_id = 1  # Admin
            new_user.theme = 'spacelab'

            # Find user-selected language in Mycodo/.language
            lang_path = os.path.join(INSTALL_DIRECTORY, ".language")
            try:
                if os.path.exists(lang_path):
                    with open(lang_path) as f:
                        language = f.read().split(":")[0]
                        if language and language in LANGUAGES:
                            new_user.language = language
            finally:
                if os.path.exists(lang_path):
                    try:
                        os.remove(lang_path)
                    except:
                        pass

            try:
                new_user.save()
                flash(gettext("User '%(user)s' successfully created. Please "
                              "log in below.", user=username),
                      "success")
                return redirect(url_for('routes_authentication.login_check'))
            except Exception as except_msg:
                flash(gettext("Failed to create user '%(user)s': %(err)s",
                              user=username,
                              err=except_msg), "error")
        else:
            utils_general.flash_form_errors(form_create_admin)

    dismiss_notification = Misc.query.first().dismiss_notification

    return render_template('create_admin.html',
                           dict_translation=TRANSLATIONS,
                           dismiss_notification=dismiss_notification,
                           form_create_admin=form_create_admin,
                           form_language=form_language,
                           form_notice=form_notice,
                           host=host,
                           language=language,
                           languages=LANGUAGES)


@blueprint.route('/login', methods=('GET', 'POST'))
def login_check():
    """Authenticate users of the web-UI."""
    if not admin_exists():
        return redirect('/create_admin')
    elif flask_login.current_user.is_authenticated:
        flash(gettext("Cannot access login page if you're already logged in"),
              "error")
        return redirect(url_for('routes_general.home'))

    settings = Misc.query.first()
    if settings.default_login_page == "password":
        return redirect(url_for('routes_authentication.login_password'))
    elif settings.default_login_page == "keypad":
        return redirect(url_for('routes_authentication.login_keypad'))
    return redirect(url_for('routes_authentication.login_password'))


@blueprint.route('/login_password', methods=('GET', 'POST'))
def login_password():
    """Authenticate users of the web-UI."""
    if not admin_exists():
        return redirect('/create_admin')
    elif flask_login.current_user.is_authenticated:
        flash(gettext("Cannot access login page if you're already logged in"),
              "error")
        return redirect(url_for('routes_general.home'))

    form_login = forms_authentication.Login()
    form_language = forms_authentication.LanguageSelect()

    language = None

    try:
        host = Misc.query.first().hostname_override
    except:
        host = None
    if not host:
        host = socket.gethostname()

    # Find user-selected language in Mycodo/.language
    try:
        lang_path = os.path.join(INSTALL_DIRECTORY, ".language")
        if os.path.exists(lang_path):
            with open(lang_path) as f:
                language_read = f.read().split(":")[0]
                if language and language in LANGUAGES:
                    language = language_read
    except:
        pass

    if session.get('language'):
        language = session['language']

    # Check if the user is banned from logging in (too many incorrect attempts)
    if banned_from_login():
        flash(gettext(
            "Too many failed login attempts. Please wait %(min)s "
            "minutes before attempting to log in again",
            min=int((LOGIN_BAN_SECONDS - session['ban_time_left']) / 60) + 1),
                "info")
    else:
        if request.method == 'POST':
            if form_language.language.data:
                session['language'] = form_language.language.data
            else:
                username = form_login.mycodo_username.data.lower()
                user_ip = request.environ.get('HTTP_X_FORWARDED_FOR', 'unknown address')
                user = User.query.filter(
                    func.lower(User.name) == username).first()

                if not user:
                    login_log(username, 'NA', user_ip, 'NOUSER')
                    failed_login()
                elif form_login.validate_on_submit():
                    matched_hash = User().check_password(
                        form_login.mycodo_password.data, user.password_hash)

                    # Encode stored password hash if it's a str
                    password_hash = user.password_hash
                    if isinstance(user.password_hash, str):
                        password_hash = user.password_hash.encode('utf-8')

                    if matched_hash == password_hash:
                        user = User.query.filter(User.name == username).first()
                        role_name = Role.query.filter(Role.id == user.role_id).first().name
                        login_log(username, role_name, user_ip, 'LOGIN')

                        # flask-login user
                        login_user = User()
                        login_user.id = user.id
                        login_user.name = user.name
                        remember_me = True if form_login.remember.data else False
                        flask_login.login_user(login_user, remember=remember_me)

                        return redirect(url_for('routes_general.home'))
                    else:
                        user = User.query.filter(User.name == username).first()
                        role_name = Role.query.filter(Role.id == user.role_id).first().name
                        login_log(username, role_name, user_ip, 'FAIL')
                        failed_login()
                else:
                    login_log(username, 'NA', user_ip, 'FAIL')
                    failed_login()

            return redirect('/login')

    return render_template('login_password.html',
                           dict_translation=TRANSLATIONS,
                           form_language=form_language,
                           form_login=form_login,
                           host=host,
                           language=language,
                           languages=LANGUAGES)


@blueprint.route('/login_keypad', methods=('GET', 'POST'))
def login_keypad():
    """Authenticate users of the web-UI (with keypad)"""
    if not admin_exists():
        return redirect('/create_admin')

    elif flask_login.current_user.is_authenticated:
        flash(gettext("Cannot access login page if you're already logged in"),
              "error")
        return redirect(url_for('routes_general.home'))

    try:
        host = Misc.query.first().hostname_override
    except:
        host = None
    if not host:
        host = socket.gethostname()

    # Check if the user is banned from logging in (too many incorrect attempts)
    if banned_from_login():
        flash(gettext(
            "Too many failed login attempts. Please wait %(min)s "
            "minutes before attempting to log in again",
            min=int((LOGIN_BAN_SECONDS - session['ban_time_left']) / 60) + 1),
                "info")

    return render_template('login_keypad.html',
                           dict_translation=TRANSLATIONS,
                           host=host)


@blueprint.route('/login_keypad_code/', methods=('GET', 'POST'))
def login_keypad_code_empty():
    """Forward to keypad when no code entered."""
    time.sleep(2)
    flash("Please enter a code", "error")
    return redirect('/login_keypad')


@blueprint.route('/login_keypad_code/<code>', methods=('GET', 'POST'))
def login_keypad_code(code):
    """Check code from keypad."""
    if not admin_exists():
        return redirect('/create_admin')

    elif flask_login.current_user.is_authenticated:
        flash(gettext("Cannot access login page if you're already logged in"),
              "error")
        return redirect(url_for('routes_general.home'))

    try:
        host = Misc.query.first().hostname_override
    except:
        host = None
    if not host:
        host = socket.gethostname()

    # Check if the user is banned from logging in (too many incorrect attempts)
    if banned_from_login():
        flash(gettext(
            "Too many failed login attempts. Please wait %(min)s "
            "minutes before attempting to log in again",
            min=int((LOGIN_BAN_SECONDS - session['ban_time_left']) / 60) + 1),
                "info")
    else:
        user = User.query.filter(User.code == code).first()
        user_ip = request.environ.get('HTTP_X_FORWARDED_FOR', 'unknown address')

        if not user:
            login_log(code, 'NA', user_ip, 'FAIL')
            failed_login()
            flash("Invalid Code", "error")
            time.sleep(2)
        else:
            role_name = Role.query.filter(Role.id == user.role_id).first().name
            login_log(user.name, role_name, user_ip, 'LOGIN')

            # flask-login user
            login_user = User()
            login_user.id = user.id
            login_user.name = user.name
            remember_me = True
            flask_login.login_user(login_user, remember=remember_me)

            return redirect(url_for('routes_general.home'))

    return render_template('login_keypad.html',
                           dict_translation=TRANSLATIONS,
                           host=host)


@blueprint.route("/logout")
@flask_login.login_required
def logout():
    """Log out of the web-ui."""
    user = User.query.filter(User.name == flask_login.current_user.name).first()
    role_name = Role.query.filter(Role.id == user.role_id).first().name
    login_log(user.name,
              role_name,
              request.environ.get('REMOTE_ADDR', 'unknown address'),
              'LOGOUT')
    # flask-login logout
    flask_login.logout_user()

    response = clear_cookie_auth()

    flash(gettext("Successfully logged out"), 'success')
    return response


@blueprint.route('/newremote/')
def newremote():
    """Verify authentication as a client computer to the remote admin."""
    username = request.args.get('user')
    pass_word = request.args.get('passw')

    user = User.query.filter(
        User.name == username).first()

    if user:
        if User().check_password(
                pass_word, user.password_hash) == user.password_hash:
            try:
                with open('/opt/Mycodo/mycodo/mycodo_flask/ssl_certs/cert.pem', 'r') as cert:
                    certificate_data = cert.read()
            except Exception:
                certificate_data = None
            return jsonify(status=0,
                           error_msg=None,
                           hash=str(user.password_hash),
                           certificate=certificate_data)
    return jsonify(status=1,
                   error_msg="Unable to authenticate with user and password.",
                   hash=None,
                   certificate=None)


@blueprint.route('/remote_login', methods=('GET', 'POST'))
def remote_admin_login():
    """Authenticate Remote Admin login."""
    password_hash = request.form.get('password_hash', None)
    username = request.form.get('username', None)

    if username and password_hash:
        user = User.query.filter(
            func.lower(User.name) == username).first()
    else:
        user = None

    if user and str(user.password_hash) == str(password_hash):
        login_user = User()
        login_user.id = user.id
        login_user.name = user.name
        flask_login.login_user(login_user, remember=False)
        return "Logged in via Remote Admin"
    else:
        return "ERROR"


@blueprint.route('/auth/')
@flask_login.login_required
def remote_auth():
    """Checks authentication for remote admin."""
    return "authenticated"


def admin_exists():
    """Verify that at least one admin user exists."""
    return User.query.filter_by(role_id=1).count()


def check_database_version_issue():
    if len(AlembicVersion.query.all()) > 1:
        flash("A check of your database indicates there is an issue with your"
              " database version number. To resolve this issue, move"
              " your mycodo.db from /opt/Mycodo/databases/mycodo.db to a "
              "different location (or delete it) and a new database will be "
              "generated in its place.", "error")


def banned_from_login():
    """Check if the person at the login prompt is banned form logging in."""
    if not session.get('failed_login_count'):
        session['failed_login_count'] = 0
    if not session.get('failed_login_ban_time'):
        session['failed_login_ban_time'] = 0
    elif session['failed_login_ban_time']:
        session['ban_time_left'] = time.time() - session['failed_login_ban_time']
        if session['ban_time_left'] < LOGIN_BAN_SECONDS:
            return 1
        else:
            session['failed_login_ban_time'] = 0
    return 0


def failed_login():
    """Count the number of failed login attempts."""
    try:
        session['failed_login_count'] += 1
    except KeyError:
        session['failed_login_count'] = 1

    if session['failed_login_count'] > LOGIN_ATTEMPTS - 1:
        session['failed_login_ban_time'] = time.time()
        session['failed_login_count'] = 0
    else:
        flash('Failed Login ({}/{})'.format(
            session['failed_login_count'], LOGIN_ATTEMPTS), "error")


def login_log(user, group, ip, status):
    """Write to login log."""
    with open(LOGIN_LOG_FILE, 'a+') as log_file:
        log_file.write(
            '{dt:%Y-%m-%d %H:%M:%S}: {stat} {user} ({grp}), {ip}\n'.format(
                dt=datetime.datetime.now(), stat=status,
                user=user, grp=group, ip=ip))


def clear_cookie_auth():
    """Delete authentication cookies."""
    response = make_response(redirect('/login'))
    session.clear()
    response.set_cookie('remember_token', '', expires=0)
    return response
