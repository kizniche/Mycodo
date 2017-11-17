# -*- coding: utf-8 -*-
import json
import logging
import requests
import sqlalchemy
import urllib3

from flask import flash
from flask import redirect
from flask import url_for

from mycodo.mycodo_flask.extensions import db
from flask_babel import gettext

from mycodo.mycodo_flask.utils import utils_general

from mycodo.databases.models import DisplayOrder
from mycodo.databases.models import Remote
from mycodo.utils.system_pi import csv_to_list_of_int
from mycodo.utils.system_pi import list_to_csv

from mycodo.mycodo_flask.utils.utils_general import add_display_order
from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.mycodo_flask.utils.utils_general import flash_form_errors

from mycodo.config import STORED_SSL_CERTIFICATE_PATH

logger = logging.getLogger(__name__)


#
# Remote host commands executed on Mycodo with Remote Admin Dashboard
#


def remote_host_auth_page(address, user, password_hash, page):
    """
    Make request, receive response, and authenticate a remote Mycodo
    connection. This checks if the HTTPS certificate matches the stored
    certificate and the user and password hash matches

    :param address: host name or IP address of remote Mycodo
    :param user: User name of an admin on the remote Mycodo
    :param password_hash: Hash of admin user's password
    :param page: The page to return information from
    :return: (1, None) for error, (0, json_data) on success
    """
    try:
        ssl_cert_file = '{path}/{file}'.format(path=STORED_SSL_CERTIFICATE_PATH,
                                               file='{add}_cert.pem'.format(
                                                    add=address))
        url = 'https://{add}/{page}/?pw_hash={hash}&user={user}'.format(
            add=address, page=page, hash=password_hash, user=user)

        # Require all certificate data matches stored certificate, except hostname
        http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED',
                                   ca_certs=ssl_cert_file,
                                   assert_hostname=False)

        r = http.request('GET', url)
        return 0, json.loads(r.data)
    except Exception as e:
        logger.exception(
            "'remote_host_auth_page' raised an exception: {err}".format(err=e))
        return 1, None


def remote_host_add(form_setup, display_order):
    """
    Add a remote Mycodo to the Remote Admin Dashboard

    Authenticate a remote Mycodo install that will be used on this system's
    Remote Admin dashboard.
    The user name and password is sent, and if verified, the password hash
    and SSL certificate is sent back.
    The hash is used to authenticate and the certificate is used to perform
    a verified SSL, in all subsequent connections.
    """
    if not utils_general.user_has_permission('edit_settings'):
        return redirect(url_for('general_routes.home'))

    if form_setup.validate():
        try:
            # Send user and password to remote Mycodo to authenticate
            credentials = {
                'user': form_setup.username.data,
                'passw': form_setup.password.data
            }
            url = 'https://{}/newremote/'.format(form_setup.host.data)
            try:
                pw_check = requests.get(url, params=credentials, verify=False).json()
            except Exception:
                return 1

            if 'status' not in pw_check:
                flash("Unknown response: {res}".format(res=pw_check), "error")
                return 1
            elif pw_check['status']:
                flash(pw_check['error_msg'], "error")
                return 1

            # Write remote certificate to file
            public_key = '{path}/{file}'.format(path=STORED_SSL_CERTIFICATE_PATH,
                                                file='{add}_cert.pem'.format(
                                                    add=form_setup.host.data))
            file_handler = open(public_key, 'w')
            file_handler.write(pw_check['certificate'])
            file_handler.close()

            new_remote_host = Remote()
            new_remote_host.host = form_setup.host.data
            new_remote_host.username = form_setup.username.data
            new_remote_host.password_hash = pw_check['hash']
            try:
                db.session.add(new_remote_host)
                db.session.commit()
                flash(gettext(u"Remote Host %(host)s with ID %(id)s (%(uuid)s)"
                              u" successfully added",
                              host=form_setup.host.data,
                              id=new_remote_host.id,
                              uuid=new_remote_host.unique_id),
                      "success")

                DisplayOrder.query.first().remote_host = add_display_order(
                    display_order, new_remote_host.id)
                db.session.commit()
            except sqlalchemy.exc.OperationalError as except_msg:
                flash(gettext(u"Remote Host Error: %(msg)s", msg=except_msg),
                      "error")
            except sqlalchemy.exc.IntegrityError as except_msg:
                flash(gettext(u"Remote Host Error: %(msg)s", msg=except_msg),
                      "error")
        except Exception as except_msg:
            flash(gettext(u"Remote Host Error: %(msg)s", msg=except_msg),
                  "error")
    else:
        flash_form_errors(form_setup)


def remote_host_del(form_setup):
    """Delete a remote Mycodo from the Remote Admin Dashboard"""
    if not utils_general.user_has_permission('edit_settings'):
        return redirect(url_for('general_routes.home'))

    try:
        delete_entry_with_id(Remote,
                             form_setup.remote_id.data)
        display_order = csv_to_list_of_int(DisplayOrder.query.first().remote_host)
        display_order.remove(int(form_setup.remote_id.data))
        DisplayOrder.query.first().remote_host = list_to_csv(display_order)
        db.session.commit()
    except Exception as except_msg:
        flash(gettext(u"Remote Host Error: %(msg)s", msg=except_msg), "error")
