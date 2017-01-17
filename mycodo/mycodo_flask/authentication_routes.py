# coding=utf-8
""" flask views that deal with user authentication """
import datetime
import socket
import time

from flask import current_app
from flask import redirect
from flask import request
from flask import render_template
from flask import flash
from flask import session
from flask import url_for
from flask import make_response
from flask_babel import gettext
from flask.blueprints import Blueprint

from mycodo import flaskforms
from flaskutils import flash_form_errors

from config import LOGIN_ATTEMPTS
from config import LOGIN_BAN_TIME_SECONDS
from config import LOGIN_LOG_FILE

from mycodo.databases.utils import session_scope
from mycodo.databases.users_db.models import Users
from mycodo.databases.mycodo_db.models import Misc

from scripts.utils import test_username, test_password


blueprint = Blueprint('authentication_routes', __name__, static_folder='../static', template_folder='../templates')


@blueprint.context_processor
def inject_hostname():
    """Variables to send with every login page request"""
    return dict(host=socket.gethostname())


@blueprint.route('/create_admin', methods=('GET', 'POST'))
def create_admin():
    if admin_exists():
        flash(gettext("Cannot access admin creation form if an admin user "
              "already exists."), "error")
        return redirect(url_for('general_routes.home'))
    form = flaskforms.CreateAdmin()
    if request.method == 'POST':
        if form.validate():
            if form.password.data != form.password_repeat.data:
                flash(gettext("Passwords do not match. Please try again."), "error")
                return redirect(url_for('general_routes.home'))
            new_user = Users()
            if test_username(form.username.data):
                new_user.user_name = form.username.data
            new_user.user_email = form.email.data
            if test_password(form.password.data):
                new_user.set_password(form.password.data)
            new_user.user_restriction = 'admin'
            new_user.user_theme = 'slate'
            try:
                with session_scope(current_app.config['USER_DB_PATH']) as db_session:
                    db_session.add(new_user)
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

    if logged_in():
        flash(gettext("Cannot access login page if you're already logged in"), "error")
        return redirect(url_for('general_routes.home'))

    form = flaskforms.Login()
    form_notice = flaskforms.InstallNotice()

    with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
        misc = db_session.query(Misc).first()
        dismiss_notification = misc.dismiss_notification
        stats_opt_out = misc.stats_opt_out

    # Check if the user is banned from logging in (too many incorrect attempts)
    if banned_from_login():
        flash(gettext("Too many failed login attempts. Please wait %(min)s "
                      "minutes before attempting to log in again",
                      min=(int(LOGIN_BAN_TIME_SECONDS - session['ban_time_left']) / 60) + 1),
              "info")
    else:
        if request.method == 'POST':
            form_name = request.form['form-name']
            if form_name == 'acknowledge':
                try:
                    with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                        mod_misc = db_session.query(Misc).first()
                        mod_misc.dismiss_notification = 1
                        db_session.commit()
                except Exception as except_msg:
                    flash(gettext("Acknowledgement unable to be saved: "
                                  "%(err)s", err=except_msg), "error")
            elif form_name == 'login' and form.validate_on_submit():
                with session_scope(current_app.config['USER_DB_PATH']) as new_session:
                    user = new_session.query(Users).filter(Users.user_name == form.username.data).first()
                    new_session.expunge_all()
                    new_session.close()
                if not user:
                    login_log(form.username.data, 'NA',
                              request.environ.get('REMOTE_ADDR', 'unknown address'), 'NOUSER')
                    failed_login()
                elif Users().check_password(form.password.data, user.user_password_hash) == user.user_password_hash:
                    login_log(user.user_name, user.user_restriction,
                              request.environ.get('REMOTE_ADDR', 'unknown address'), 'LOGIN')
                    session['logged_in'] = True
                    session['user_group'] = user.user_restriction
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
                    login_log(user.user_name, user.user_restriction,
                              request.environ.get('REMOTE_ADDR', 'unknown address'), 'FAIL')
                    failed_login()
            else:
                login_log(form.username.data, 'NA',
                          request.environ.get('REMOTE_ADDR', 'unknown address'), 'FAIL')
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
                  session['user_group'],
                  request.environ.get('REMOTE_ADDR', 'unknown address'),
                  'LOGOUT')
    response = clear_cookie_auth()
    flash(gettext("Successfully logged out"), 'success')
    return response


def admin_exists():
    """Verify that at least one admin user exists"""
    with session_scope(current_app.config['USER_DB_PATH']) as new_session:
        return new_session.query(Users).filter(Users.user_restriction == 'admin').count()


def authenticate_cookies(db_path, users):
    """Check for cookies to authenticate Login"""
    cookie_username = request.cookies.get('user_name')
    cookie_password_hash = request.cookies.get('user_pass_hash')
    if cookie_username is not None:
        with session_scope(db_path) as new_session:
            user = new_session.query(users).filter(
                users.user_name == cookie_username).first()
            new_session.expunge_all()
            new_session.close()
            if user is None:
                return False
            elif cookie_password_hash == user.user_password_hash:
                session['logged_in'] = True
                session['user_group'] = user.user_restriction
                session['user_name'] = user.user_name
                session['user_theme'] = user.user_theme
                return True
            else:
                failed_login()
    return False


def logged_in():
    """Verify the user is logged in"""
    if (not session.get('logged_in') and
            not authenticate_cookies(current_app.config['USER_DB_PATH'], Users)):
        return 0
    elif (session.get('logged_in') or
            (not session.get('logged_in') and
                authenticate_cookies(current_app.config['USER_DB_PATH'], Users))):
        return 1


def banned_from_login():
    """Check if the person at the login prompt is banned form logging in"""
    if not session.get('failed_login_count'):
        session['failed_login_count'] = 0
    if not session.get('failed_login_ban_time'):
        session['failed_login_ban_time'] = 0
    elif session['failed_login_ban_time']:
        session['ban_time_left'] = time.time() - session['failed_login_ban_time']
        if session['ban_time_left'] < LOGIN_BAN_TIME_SECONDS:
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
        log_file.write('{:%Y-%m-%d %H:%M:%S}: {} {} ({}), {}\n'.format(
            datetime.datetime.now(), status, user, group, ip))


def clear_cookie_auth():
    """Delete authentication cookies"""
    response = make_response(redirect('/login'))
    session.clear()  # or session['logged_in'] = False
    response.set_cookie('user_name', '', expires=0)
    response.set_cookie('user_pass_hash', '', expires=0)
    return response
