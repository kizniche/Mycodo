# coding=utf-8
""" flask views that deal with user authentication """
import json
import logging
import socket
import flask_login

from flask import redirect
from flask import request
from flask import render_template
from flask import url_for

from flask.blueprints import Blueprint

from mycodo.databases.models import DisplayOrder
from mycodo.databases.models import Remote

from mycodo.mycodo_flask.forms import forms_authentication
from mycodo.mycodo_flask.utils import utils_remote_host
from mycodo.mycodo_flask.utils import utils_general


blueprint = Blueprint(
    'remote_admin_routes',
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
        return redirect(url_for('general_routes.home'))

    remote_hosts = Remote.query.all()
    display_order_unsplit = DisplayOrder.query.first().remote_host
    if display_order_unsplit:
        display_order = display_order_unsplit.split(",")
    else:
        display_order = []

    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    host_auth = {}
    host_inputs = {}
    for each_host in remote_hosts:
        # Return whether a hosts were authenticated
        host_auth[each_host.host] = utils_remote_host.auth_credentials(
            each_host.host, each_host.username, each_host.password_hash)

        # Return input information about each host
        host_inputs[each_host.host] = json.loads(
            utils_remote_host.remote_get_inputs(each_host.host,
                                                each_host.username,
                                                each_host.password_hash))

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
        return redirect(url_for('general_routes.home'))

    remote_hosts = Remote.query.all()
    display_order_unsplit = DisplayOrder.query.first().remote_host
    if display_order_unsplit:
        display_order = display_order_unsplit.split(",")
    else:
        display_order = []

    form_setup = forms_authentication.RemoteSetup()
    host_auth = {}
    for each_host in remote_hosts:
        host_auth[each_host.host] = utils_remote_host.auth_credentials(
            each_host.host, each_host.username, each_host.password_hash)

    if request.method == 'POST':
        if form_setup.add.data:
            utils_remote_host.remote_host_add(form_setup,
                                              display_order)
        elif form_setup.delete.data:
            utils_remote_host.remote_host_del(form_setup)
        return redirect('/remote/setup')

    return render_template('remote/setup.html',
                           form_setup=form_setup,
                           display_order=display_order,
                           remote_hosts=remote_hosts,
                           host_auth=host_auth)
