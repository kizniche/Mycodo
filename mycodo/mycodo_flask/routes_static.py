# coding=utf-8
import logging
import operator
import os
import socket
import subprocess
import traceback
from io import BytesIO

import flask_login
from flask import (current_app, redirect, render_template, request,
                   send_from_directory, url_for)
from flask import send_file
from flask.blueprints import Blueprint

from mycodo.config import (ALEMBIC_VERSION, INSTALL_DIRECTORY, LANGUAGES,
                           MYCODO_VERSION, THEMES, THEMES_DARK)
from mycodo.config import PATH_STATIC
from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import Dashboard, Misc
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


def template_exists(path):
    path_start = "{}/mycodo/mycodo_flask/templates".format(INSTALL_DIRECTORY)
    path_full = "{}/{}".format(path_start, path)
    if os.path.exists(path_full) and os.path.abspath(path_full).startswith(path_start):
        return True


@blueprint.context_processor
def inject_variables():
    """Variables to send with every page request."""
    form_dashboard = forms_dashboard.DashboardConfig()  # Dashboard configuration in layout

    dashboards = Dashboard.query.all()
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

    languages_sorted = sorted(LANGUAGES.items(), key=operator.itemgetter(1))

    return dict(current_user=flask_login.current_user,
                custom_css=misc.custom_css,
                dark_themes=THEMES_DARK,
                daemon_status=daemon_status,
                dashboards=dashboards,
                form_dashboard=form_dashboard,
                hide_alert_info=misc.hide_alert_info,
                hide_alert_success=misc.hide_alert_success,
                hide_alert_warning=misc.hide_alert_warning,
                hide_tooltips=misc.hide_tooltips,
                host=socket.gethostname(),
                languages=languages_sorted,
                mycodo_version=MYCODO_VERSION,
                permission_view_settings=user_has_permission('view_settings', silent=True),
                dict_translation=TRANSLATIONS,
                settings=misc,
                template_exists=template_exists,
                themes=THEMES,
                upgrade_available=misc.mycodo_upgrade_available)


@blueprint.app_errorhandler(404)
def not_found(error):
    return render_template('404.html', error=error), 404


@blueprint.route('/favicon.png')
def favicon():
    """Return favicon image"""
    misc = Misc.query.first()

    if misc.favicon_display == 'default':
        return send_from_directory(os.path.join(PATH_STATIC, 'img'), "favicon.png")
    else:
        return send_file(
            BytesIO(misc.brand_favicon),
            mimetype='image/png'
        )


@blueprint.route('/robots.txt')
def static_from_root():
    """Return static robots.txt."""
    return send_from_directory(current_app.static_folder, request.path[1:])


# @blueprint.route("/mycodo-manual_{}.pdf".format(MYCODO_VERSION))
# def download_pdf_manual():
#     """Return PDF Manual."""
#     path_manual = os.path.join(INSTALL_DIRECTORY, "docs")
#     return send_from_directory(path_manual, "mycodo-manual.pdf")


@blueprint.app_errorhandler(404)
def not_found(error):
    return render_template('404.html', error=error), 404


@blueprint.app_errorhandler(500)
def page_error(error):
    try:
        trace = traceback.format_exc()
    except:
        trace = None

    try:
        lsb_release = subprocess.Popen(
            "lsb_release -irdc", stdout=subprocess.PIPE, shell=True)
        (lsb_release_output, _) = lsb_release.communicate()
        lsb_release.wait()
        if lsb_release_output:
            lsb_release_output = lsb_release_output.decode("latin1").replace("\n", "<br/>")
    except:
        lsb_release_output = None

    try:
        model = subprocess.Popen(
            "cat /proc/device-tree/model && echo", stdout=subprocess.PIPE, shell=True)
        (model_output, _) = model.communicate()
        model.wait()
        if model_output:
            model_output = model_output.decode("latin1")
    except:
        model_output = None

    dict_return = {
        "trace": trace,
        "version_mycodo": MYCODO_VERSION,
        "version_alembic":  ALEMBIC_VERSION,
        "lsb_release": lsb_release_output,
        "model": model_output
    }

    return render_template('500.html', dict_return=dict_return), 500
