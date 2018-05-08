# coding=utf-8
import logging
import socket
import traceback

from flask import current_app
from flask import redirect
from flask import render_template
from flask import request
from flask import send_from_directory
from flask import url_for
from flask.blueprints import Blueprint

from mycodo.config import MYCODO_VERSION
from mycodo.config import THEMES_DARK
from mycodo.databases.models import Misc
from mycodo.mycodo_client import DaemonControl
from mycodo.mycodo_flask.routes_authentication import admin_exists

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
    try:
        control = DaemonControl()
        daemon_status = control.daemon_status()
    except Exception as e:
        logger.error("URL for 'inject_variables' raised and error: "
                     "{err}".format(err=e))
        daemon_status = '0'

    misc = Misc.query.first()
    return dict(daemon_status=daemon_status,
                dark_themes=THEMES_DARK,
                mycodo_version=MYCODO_VERSION,
                host=socket.gethostname(),
                hide_alert_success=misc.hide_alert_success,
                hide_alert_info=misc.hide_alert_info,
                hide_alert_warning=misc.hide_alert_warning,
                hide_tooltips=misc.hide_tooltips,
                upgrade_available = misc.mycodo_upgrade_available)


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
