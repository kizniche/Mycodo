# coding=utf-8
""" flask views that deal with user authentication """
import datetime
import logging
import socket
import time

from flask import (
    redirect,
    request,
    render_template,
    flash,
    session,
    url_for,
    make_response
)
from flask_babel import gettext
from flask.blueprints import Blueprint

# Classes
from mycodo.databases.mycodo_db.models import (
    db,
    AlembicVersion,
    Misc,
    User
)

# Functions
from mycodo import flaskforms
from mycodo.flaskutils import flash_form_errors
from mycodo.scripts.utils import (
    test_username,
    test_password
)

# Config
from config import (
    LOGIN_ATTEMPTS,
    LOGIN_BAN_SECONDS,
    LOGIN_LOG_FILE
)

blueprint = Blueprint(
    'authentication_routes',
    __name__,
    static_folder='../static',
    template_folder='../templates'
)

logger = logging.getLogger(__name__)


@blueprint.context_processor
def inject_hostname():
    """Variables to send with every login page request"""
    return dict(host=socket.gethostname())


@blueprint.route('/create_admin', methods=('GET', 'POST'))
def create_admin():
    if admin_exists():
        flash(gettext(
            "Cannot access admin creation form if an admin user "
            "already exists."), "error")
        return redirect(url_for('general_routes.home'))
    form = flaskforms.CreateAdmin()
    if request.method == 'POST':
        if form.validate():
            error = False
            if form.password.data != form.password_repeat.data:
                flash(gettext("Passwords do not match. Please try again."),
                      "error")
                error = True
            if not test_username(form.username.data):
                flash(gettext(
                    "Invalid user name. Must be between 2 and 64 characters "
                    "and only contain letters and numbers."),
                    "error")
                error = True
            if not test_password(form.password.data):
                flash(gettext(
                    "Invalid password. Must be between 6 and 64 characters "
                    "and only contain letters, numbers, and symbols."),
                      "error")
                error = True
            if error:
                return redirect(url_for('general_routes.home'))

            new_user = User()
            new_user.user_name = form.username.data
            new_user.user_email = form.email.data
            new_user.set_password(form.password.data)
            new_user.user_role = 1  # Admin
            new_user.user_theme = 'slate'
            try:
                db.session.add(new_user)
                db.session.commit()
                flash(gettext("User '%(user)s' successfully created. Please "
                              "log in below.", user=form.username.data),
                      "success")
                return redirect(url_for('authentication_routes.do_login'))
            except Exception as except_msg:
                flash(gettext("Failed to create user '%(user)s': %(err)s",
                              user=form.username.data,
                              err=except_msg), "error")
        else:
            flash_form_errors(form)
    return render_template('create_admin.html',
                           form=form)


@blueprint.route('/login', methods=('GET', 'POST'))
def do_login():
    """Authenticate users of the web-UI"""
    if not admin_exists():
        return redirect('/create_admin')

    elif logged_in():
        flash(gettext("Cannot access login page if you're already logged in"),
              "error")
        return redirect(url_for('general_routes.home'))

    form = flaskforms.Login()
    form_notice = flaskforms.InstallNotice()

    misc = Misc.query.first()
    dismiss_notification = misc.dismiss_notification
    stats_opt_out = misc.stats_opt_out

    # Check if the user is banned from logging in (too many incorrect attempts)
    if banned_from_login():
        flash(gettext(
            "Too many failed login attempts. Please wait %(min)s "
            "minutes before attempting to log in again",
            min=(int(LOGIN_BAN_SECONDS - session['ban_time_left']) / 60) + 1),
                "info")
    else:
        if request.method == 'POST':
            form_name = request.form['form-name']
            if form_name == 'acknowledge':
                try:
                    mod_misc = Misc.query.first()
                    mod_misc.dismiss_notification = 1
                    db.session.commit()
                except Exception as except_msg:
                    flash(gettext("Acknowledgement unable to be saved: "
                                  "%(err)s", err=except_msg), "error")
            elif form_name == 'login' and form.validate_on_submit():
                user = User.query.filter(
                    User.user_name == form.username.data).first()
                if not user:
                    login_log(form.username.data,
                              'NA',
                              request.environ.get(
                                  'REMOTE_ADDR', 'unknown address'),
                              'NOUSER')
                    failed_login()
                elif User().check_password(
                        form.password.data,
                        user.user_password_hash) == user.user_password_hash:
                    login_log(user.user_name,
                              user.role.name,
                              request.environ.get('REMOTE_ADDR',
                                                  'unknown address'),
                              'LOGIN')
                    session['logged_in'] = True
                    session['user_role'] = user.role.name
                    session['user_name'] = user.user_name
                    session['user_theme'] = user.user_theme
                    if form.remember.data:
                        response = make_response(redirect('/'))
                        expire_date = datetime.datetime.now()
                        expire_date = expire_date + datetime.timedelta(days=90)
                        response.set_cookie('user_name',
                                            user.user_name,
                                            expires=expire_date)
                        response.set_cookie('user_pass_hash',
                                            user.user_password_hash,
                                            expires=expire_date)
                        return response
                    return redirect(url_for('general_routes.home'))
                else:
                    login_log(user.user_name,
                              user.role.name,
                              request.environ.get('REMOTE_ADDR',
                                                  'unknown address'),
                              'FAIL')
                    failed_login()
            else:
                login_log(form.username.data,
                          'NA',
                          request.environ.get('REMOTE_ADDR',
                                              'unknown address'),
                          'FAIL')
                failed_login()

            return redirect('/login')

    return render_template('login.html',
                           form=form,
                           formNotice=form_notice,
                           dismiss_notification=dismiss_notification,
                           stats_opt_out=stats_opt_out)


@blueprint.route("/logout")
def logout():
    """Log out of the web-ui"""
    if session.get('user_name'):
        login_log(session['user_name'],
                  session['user_role'],
                  request.environ.get('REMOTE_ADDR', 'unknown address'),
                  'LOGOUT')
    response = clear_cookie_auth()
    flash(gettext("Successfully logged out"), 'success')
    return response


def admin_exists():
    """Verify that at least one admin user exists"""
    return User.query.filter(User.user_role == 1).count()


def authenticate_cookies():
    """Check for cookies to authenticate Login"""
    cookie_username = request.cookies.get('user_name')
    cookie_password_hash = request.cookies.get('user_pass_hash')
    if cookie_username is not None:
        user = User.query.filter(
            User.user_name == cookie_username).first()

        if user is None:
            return False
        elif cookie_password_hash == user.user_password_hash:
            session['logged_in'] = True
            session['user_role'] = user.role.name
            session['user_name'] = user.user_name
            session['user_theme'] = user.user_theme
            return True
        else:
            failed_login()
    return False


def check_database_version_issue():
    if len(AlembicVersion.query.all()) > 1:
        flash("A check of your database indicates there is an issue with your"
              " database version number. This issue first appeared in early "
              "4.1.x versions of Mycodo and has since been resolved. However,"
              " even though things may seem okay, this issue prevents your "
              "database from being upgraded properly. Therefore, if you "
              "continue to use Mycodo without regenerating your database, you"
              " will assuredly experience issues. To resolve this issue, move"
              " your mycodo.db from ~/Mycodo/databases/mycodo.db to a "
              "different location (or delete it) and a new database will be "
              "generated in its place. You will need to configure Mycodo from"
              " scratch, but this is the only way to ensure your database is "
              "able to be upgraded when the time comes. Sorry for the "
              "inconvenience.", "error")


def logged_in():
    """Verify the user is logged in"""
    check_database_version_issue()
    if (not session.get('logged_in') and
            not authenticate_cookies()):
        return 0
    elif (session.get('logged_in') or
            (not session.get('logged_in') and
                authenticate_cookies())):
        return 1


def banned_from_login():
    """Check if the person at the login prompt is banned form logging in"""
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
    """Count the number of failed login attempts"""
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
    """Write to login log"""
    with open(LOGIN_LOG_FILE, 'a') as log_file:
        log_file.write(
            '{dt:%Y-%m-%d %H:%M:%S}: {stat} {user} ({grp}), {ip}\n'.format(
                dt=datetime.datetime.now(), stat=status,
                user=user, grp=group, ip=ip))


def clear_cookie_auth():
    """Delete authentication cookies"""
    response = make_response(redirect('/login'))
    session.clear()  # or session['logged_in'] = False
    response.set_cookie('user_name', '', expires=0)
    response.set_cookie('user_pass_hash', '', expires=0)
    return response
