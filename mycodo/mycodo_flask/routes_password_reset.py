# coding=utf-8
"""flask views that deal with password reset."""
import datetime
import logging
import socket
import string

import os
import random
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask.blueprints import Blueprint
from flask_babel import gettext

from mycodo.config import INSTALL_DIRECTORY
from mycodo.databases.models import Role
from mycodo.databases.models import SMTP
from mycodo.databases.models import User
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.forms import forms_authentication
from mycodo.utils.send_data import send_email
from mycodo.utils.utils import test_password

logger = logging.getLogger(__name__)

blueprint = Blueprint(
    'routes_password_reset',
    __name__,
    static_folder='../static',
    template_folder='../templates'
)


@blueprint.route('/forgot_password', methods=('GET', 'POST'))
def forgot_password():
    """Page to send password reset email."""
    error = []
    form_forgot_password = forms_authentication.ForgotPassword()

    if request.method == 'POST':
        if form_forgot_password.submit.data:
            if not form_forgot_password.username.data:
                user = None
                error.append("User name cannot be left blank")
            else:
                user = User.query.filter(User.name == form_forgot_password.username.data.lower()).first()

            if not error:
                # test if user name exists
                if user:
                    # check last time requested
                    if user.password_reset_last_request:
                        difference = datetime.datetime.now() - user.password_reset_last_request
                        if difference.seconds < 1800:
                            error.append("Requesting too many password resets")

                    role = Role.query.filter(Role.id == user.role_id).first()
                    if not role or not role.reset_password:
                        error.append("Cannot reset password of this user")

            if not error:
                if user:
                    user.password_reset_code = generate_reset_code(30)
                    user.password_reset_code_expiration = datetime.datetime.now() + datetime.timedelta(minutes=30)
                    db.session.commit()

                hostname = socket.gethostname()
                now = datetime.datetime.now()

                if form_forgot_password.reset_method.data == 'email':
                    smtp = SMTP.query.first()
                    if user and smtp.host and smtp.protocol and smtp.port and smtp.user and smtp.passw:
                        subject = "Mycodo Password Reset ({})".format(hostname)
                        msg = "A password reset has been requested for user {user} on host {host} at {time} " \
                              "with your email address.\n\nIf you did not initiate this, you can disregard " \
                              "this email.\n\nIf you would like to reset your password, the password reset " \
                              "code below will be good for the next 30 minutes.\n\n{code}".format(
                                user=user.name,
                                host=hostname,
                                time=now.strftime("%d/%m/%Y %H:%M"),
                                code=user.password_reset_code)
                        send_email(
                            smtp.host, smtp.protocol, smtp.port,
                            smtp.user, smtp.passw, smtp.email_from,
                            user.email, msg, subject=subject)
                    flash("If the user name exists, it has a valid email associated with it, and the email "
                          "server settings are configured correctly, an email will be sent with instructions "
                          "for resetting your password.", "success")
                elif form_forgot_password.reset_method.data == 'file':
                    save_path = os.path.join(INSTALL_DIRECTORY, "password_reset.txt")
                    if user:
                        with open(save_path, 'w') as out_file:
                            msg = "A password reset has been requested for user {user} on host {host} at " \
                                  "{time}.\n\nIf you would like to reset your password, the password reset " \
                                  "code below will be good for the next 30 minutes.\n\n{code}\n".format(
                                    user=user.name,
                                    host=hostname,
                                    time=now.strftime("%d/%m/%Y %H:%M"),
                                    code=user.password_reset_code)
                            out_file.write(msg)
                    flash("If the user name exists, a file will be created at {} with instructions "
                          "for resetting your password.".format(save_path), "success")
            if error:
                for each_error in error:
                    flash(each_error, "error")
            else:
                return redirect(url_for('routes_password_reset.reset_password'))

    return render_template('forgot_password.html',
                           form_forgot_password=form_forgot_password)


@blueprint.route('/reset_password', methods=('GET', 'POST'))
def reset_password():
    """Page to reset user password."""
    error = []
    form_reset_password = forms_authentication.ResetPassword()

    if request.method == 'POST' and form_reset_password.submit.data:
        if not form_reset_password.password_reset_code.data:
            error.append("Must enter a reset code")
        if not form_reset_password.password.data or not form_reset_password.password_repeat.data:
            error.append("Must enter a password")
        if form_reset_password.password.data != form_reset_password.password_repeat.data:
            error.append("Passwords do not match")
        if not test_password(form_reset_password.password.data):
            error.append(gettext(
                "Invalid password. Must be between 6 and 64 characters "
                "and only contain letters, numbers, and symbols."))

        if not error:
            wrong_code_msg = gettext("Code expired or invalid")
            # Check if code exists
            user = User.query.filter(User.password_reset_code == form_reset_password.password_reset_code.data).first()

            if user:
                # code found, now check if code has expired
                if datetime.datetime.now() > user.password_reset_code_expiration:
                    error.append(wrong_code_msg)
                    user.password_reset_code_expiration = None
                    user.password_reset_code = None
                    user.password_reset_last_request = None
                    db.session.commit()
                else:
                    user.set_password(form_reset_password.password.data)
                    user.password_reset_code_expiration = None
                    user.password_reset_code = None
                    user.password_reset_last_request = None
                    db.session.commit()
                    flash("Password successfully reset", "success")
                    return redirect(url_for('routes_authentication.login_check'))
            else:
                error.append(wrong_code_msg)

        if error:
            for each_error in error:
                flash(each_error, "error")

    return render_template('reset_password.html',
                           form_reset_password=form_reset_password)


def generate_reset_code(length):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))
