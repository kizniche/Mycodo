# coding=utf-8
""" flask views that deal with user authentication """
import datetime

from flask import redirect
from flask import request
from flask import render_template
from flask import flash
from flask import session
from flask import make_response
from flask.blueprints import Blueprint

from mycodo import flaskutils, flaskforms

from mycodo.databases.utils import session_scope
from mycodo.databases.users_db.models import Users
from mycodo.databases.mycodo_db.models import Misc

from config import MYCODO_DB_PATH
from config import USER_DB_PATH

blueprint = Blueprint('authentication', __name__, static_folder='../static', template_folder='../templates')


@blueprint.route('/login', methods=('GET', 'POST'))
def do_admin_login():
    """Authenticate users of the web-UI"""
    # Check if the user is banned from logging in
    if flaskutils.banned_from_login():
        return redirect('/')

    form = flaskforms.Login()
    form_notice = flaskforms.InstallNotice()

    with session_scope(MYCODO_DB_PATH) as db_session:
        misc = db_session.query(Misc).first()
        dismiss_notification = misc.dismiss_notification
        stats_opt_out = misc.stats_opt_out

    if request.method == 'POST':
        form_name = request.form['form-name']
        if form_name == 'acknowledge':
            try:
                with session_scope(MYCODO_DB_PATH) as db_session:
                    mod_misc = db_session.query(Misc).first()
                    mod_misc.dismiss_notification = 1
                    db_session.commit()
            except Exception as except_msg:
                flash("Acknowledgement not saved: {}".format(except_msg), "error")
        elif form_name == 'login' and form.validate_on_submit():
            with session_scope(USER_DB_PATH) as new_session:
                user = new_session.query(Users).filter(Users.user_name == form.username.data).first()
                new_session.expunge_all()
                new_session.close()
            if not user:
                flaskutils.login_log(form.username.data, 'NA',
                                     request.environ.get('REMOTE_ADDR', 'unknown address'), 'NOUSER')
                flaskutils.failed_login()
            elif Users().check_password(form.password.data, user.user_password_hash) == user.user_password_hash:
                flaskutils.login_log(user.user_name, user.user_restriction,
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
                return redirect('/')
            else:
                flaskutils.login_log(user.user_name, user.user_restriction,
                                     request.environ.get('REMOTE_ADDR', 'unknown address'), 'FAIL')
                flaskutils.failed_login()
        else:
            flaskutils.login_log(form.username.data, 'NA',
                                 request.environ.get('REMOTE_ADDR', 'unknown address'), 'FAIL')
            flaskutils.failed_login()

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
        flaskutils.login_log(session['user_name'], session['user_group'],
                             request.environ.get('REMOTE_ADDR', 'unknown address'), 'LOGOUT')
    response = flaskutils.clear_cookie_auth()
    flash('Successfully logged out', 'success')
    return response

