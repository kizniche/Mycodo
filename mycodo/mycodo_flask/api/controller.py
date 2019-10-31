# coding=utf-8
import logging
import traceback

import flask_login
from flask_accept import accept
from flask_restplus import Namespace
from flask_restplus import Resource
from flask_restplus import abort

from mycodo.mycodo_client import DaemonControl
from mycodo.mycodo_flask.utils import utils_general

logger = logging.getLogger(__name__)

ns_controller = Namespace('controller', description='Controller operations')

default_responses = {
    200: 'Success',
    401: 'Invalid API Key',
    403: 'Insufficient Permissions',
    404: 'Not Found',
    422: 'Unprocessable Entity',
    429: 'Too Many Requests',
    460: 'Fail',
    500: 'Internal Server Error'
}


@ns_controller.route('/controller/activate/<string:controller_type>/<string:unique_id>')
@ns_controller.doc(
    security='apikey',
    responses=default_responses,
    params={
        'controller_type': 'The type of controller (e.g. Conditional, Custom, Input, LCD, Math, PID, Trigger).',
        'unique_id': 'The unique ID of the controller.'
    }
)
class OutputPWM(Resource):
    """Controller activate"""

    @accept('application/vnd.mycodo.v1+json')
    @flask_login.login_required
    def post(self, controller_type, unique_id):
        """Activate a controller"""
        if not utils_general.user_has_permission('edit_controllers'):
            abort(403)

        try:
            control = DaemonControl()
            activate = control.controller_activate(controller_type, unique_id)
            if activate[0]:
                return {'message': activate[1]}, 460
            else:
                return {'message': activate[1]}, 200
        except Exception:
            abort(500, custom=traceback.format_exc())


@ns_controller.route('/controller/deactivate/<string:controller_type>/<string:unique_id>')
@ns_controller.doc(
    security='apikey',
    responses=default_responses,
    params={
        'controller_type': 'The type of controller (e.g. Conditional, Custom, Input, LCD, Math, PID, Trigger).',
        'unique_id': 'The unique ID of the controller.'
    }
)
class OutputPWM(Resource):
    """Controller deactivate"""

    @accept('application/vnd.mycodo.v1+json')
    @flask_login.login_required
    def post(self, controller_type, unique_id):
        """Deactivate a controller"""
        if not utils_general.user_has_permission('edit_controllers'):
            abort(403)

        try:
            control = DaemonControl()
            activate = control.controller_deactivate(controller_type, unique_id)
            if activate[0]:
                return {'message': activate[1]}, 460
            else:
                return {'message': activate[1]}, 200
        except Exception:
            abort(500, custom=traceback.format_exc())
