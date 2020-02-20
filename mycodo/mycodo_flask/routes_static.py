# coding=utf-8
import logging
import socket
import traceback

import flask_login
from flask import current_app
from flask import redirect
from flask import render_template
from flask import request
from flask import send_from_directory
from flask import url_for
from flask.blueprints import Blueprint

from mycodo.config import MYCODO_VERSION
from mycodo.config import THEMES_DARK
from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import Dashboard
from mycodo.databases.models import Misc
from mycodo.mycodo_client import DaemonControl
from mycodo.mycodo_flask.forms import forms_dashboard
from mycodo.mycodo_flask.routes_authentication import admin_exists
from mycodo.mycodo_flask.utils.utils_general import user_has_permission

blueprint = Blueprint('routes_static',
                      __name__,
                      static_folder='../static',
                      template_folder='../templates')

logger = logging.getLogger(__name__)


def before_request_admin_exist():
    """
    Ensure databases exist and at least one user is in the user database.
    """
    if not admin_exists():
        return redirect(url_for("routes_authentication.create_admin"))
blueprint.before_request(before_request_admin_exist)


@blueprint.context_processor
def inject_variables():
    """Variables to send with every page request"""
    form_dashboard = forms_dashboard.DashboardConfig()  # Dashboard configuration in layout

    misc = Misc.query.first()

    try:
        if not current_app.config['TESTING']:
            control = DaemonControl()
            daemon_status = control.daemon_status()
        else:
            daemon_status = '0'
    except Exception as e:
        logger.debug("URL for 'inject_variables' raised and error: "
                     "{err}".format(err=e))
        daemon_status = '0'

    dashboards = []
    for each_dash in Dashboard.query.all():
        dashboards.append({
            'dashboard_id': each_dash.unique_id,
            'name': each_dash.name
        })

    return dict(dark_themes=THEMES_DARK,
                daemon_status=daemon_status,
                dashboards=dashboards,
                form_dashboard=form_dashboard,
                hide_alert_info=misc.hide_alert_info,
                hide_alert_success=misc.hide_alert_success,
                hide_alert_warning=misc.hide_alert_warning,
                hide_tooltips=misc.hide_tooltips,
                host=socket.gethostname(),
                mycodo_version=MYCODO_VERSION,
                permission_view_settings=user_has_permission('view_settings', silent=True),
                dict_translation=TRANSLATIONS,
                upgrade_available=misc.mycodo_upgrade_available,
                username=flask_login.current_user.name)


@blueprint.route('/robots.txt')
def static_from_root():
    """Return static robots.txt"""
    return send_from_directory(current_app.static_folder, request.path[1:])


@blueprint.app_errorhandler(404)
def not_found(error):
    return render_template('404.html', error=error), 404


@blueprint.app_errorhandler(500)
def page_error(error):
    trace = traceback.format_exc()
    return render_template('500.html', trace=trace), 500
