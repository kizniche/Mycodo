# coding=utf-8
import flask_login
import logging
import threading
import traceback
from flask_accept import accept
from flask_restx import Resource
from flask_restx import abort
from flask_restx import fields

from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import Input
from mycodo.databases.models import InputChannel
from mycodo.databases.models.input import InputChannelSchema
from mycodo.databases.models.input import InputSchema
from mycodo.databases.models.measurement import DeviceMeasurementsSchema
from mycodo.mycodo_client import DaemonControl
from mycodo.mycodo_flask.api import api
from mycodo.mycodo_flask.api import default_responses
from mycodo.mycodo_flask.api.utils import get_from_db
from mycodo.mycodo_flask.api.utils import return_list_of_dictionaries
from mycodo.mycodo_flask.routes_admin import install_dependencies
from mycodo.mycodo_flask.utils import utils_general
from mycodo.mycodo_flask.utils.utils_general import return_dependencies

logger = logging.getLogger(__name__)

ns_dep = api.namespace('dependency', description='Dependency operations')


@ns_dep.route('/install/device/<string:device_name>')
@ns_dep.doc(
    security='apikey',
    responses=default_responses,
    params={'device_name': 'The device name to install dependencies for.'}
)
class DependencyInstall(Resource):
    """Install all dependencies for a device"""

    @accept('application/vnd.mycodo.v1+json')
    @flask_login.login_required
    def get(self, device_name):
        """Install all dependencies for a device."""
        if not utils_general.user_has_permission('edit_controllers'):
            abort(403)
        try:
            device_unmet_dependencies, _, _ = return_dependencies(device_name)
            install_deps = threading.Thread(
                target=install_dependencies,
                args=(device_unmet_dependencies,))
            install_deps.start()

            return {
                'success': True,
                'message': 'dependency install initiated'
            }, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())
