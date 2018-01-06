# coding=utf-8
""" flask views that deal with user authentication """
import json
import logging
import socket

import flask_login
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask.blueprints import Blueprint

from mycodo.databases.models import DisplayOrder
from mycodo.databases.models import Remote
from mycodo.mycodo_flask.forms import forms_authentication
from mycodo.mycodo_flask.utils import utils_general
from mycodo.mycodo_flask.utils import utils_remote_host
from mycodo.mycodo_flask.utils.utils_remote_host import remote_host_page
from mycodo.mycodo_flask.utils.utils_remote_host import remote_log_in

blueprint = Blueprint(
    'routes_remote_admin',
    __name__,
    static_folder='../static',
    template_folder='../templates'
)

logger = logging.getLogger(__name__)


@blueprint.context_processor
def inject_hostname():
    """Variables to send with every login page request"""
    return dict(host=socket.gethostname())


@blueprint.route('/remote/input', methods=('GET', 'POST'))
@flask_login.login_required
def remote_input():
    """Returns input information for remote administration"""
    if not utils_general.user_has_permission('edit_settings'):
        return redirect(url_for('routes_general.home'))

    remote_hosts = Remote.query.all()
    display_order_unsplit = DisplayOrder.query.first().remote_host
    if display_order_unsplit:
        display_order = display_order_unsplit.split(",")
    else:
        display_order = []

    host_auth = {}
    host_inputs = {}
    for each_host in remote_hosts:
        # Return input information about each host
        headers = remote_log_in(
            each_host.host, each_host.username, each_host.password_hash)

        _, host_inputs[each_host.host] = remote_host_page(
            each_host.host, headers, 'remote_get_inputs')

        host_inputs[each_host.host] = json.loads(host_inputs[each_host.host])

    return render_template('remote/input.html',
                           display_order=display_order,
                           remote_hosts=remote_hosts,
                           host_auth=host_auth,
                           host_inputs=host_inputs)


@blueprint.route('/remote/setup', methods=('GET', 'POST'))
@flask_login.login_required
def remote_setup():
    """Return pages for remote administration"""
    if not utils_general.user_has_permission('edit_settings'):
        return redirect(url_for('routes_general.home'))

    remote_hosts = Remote.query.all()
    display_order_unsplit = DisplayOrder.query.first().remote_host
    if display_order_unsplit:
        display_order = display_order_unsplit.split(",")
    else:
        display_order = []

    form_setup = forms_authentication.RemoteSetup()

    if request.method == 'POST':
        if form_setup.add.data:
            utils_remote_host.remote_host_add(form_setup,
                                              display_order)
        elif form_setup.delete.data:
            utils_remote_host.remote_host_del(form_setup)
        return redirect('/remote/setup')

    host_auth = {}
    for each_host in remote_hosts:
        headers = remote_log_in(
            each_host.host, each_host.username, each_host.password_hash)

        _, host_auth[each_host.host] = remote_host_page(
            each_host.host, headers, 'auth')

    return render_template('remote/setup.html',
                           form_setup=form_setup,
                           display_order=display_order,
                           remote_hosts=remote_hosts,
                           host_auth=host_auth)
