# coding=utf-8
import logging
import traceback

import flask_login
from flask_accept import accept
from flask_restplus import Namespace
from flask_restplus import Resource
from flask_restplus import abort
from flask_restplus import fields

from mycodo.mycodo_client import DaemonControl
from mycodo.mycodo_flask.utils import utils_general

logger = logging.getLogger(__name__)

ns_controller = Namespace('controllers', description='Controller operations')

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

controller_status_fields = ns_controller.model('Controller Status Fields', {
    'is_active': fields.Boolean
})

controller_set_fields = ns_controller.model('Controller Modulation Fields', {
    'activate': fields.Boolean(
        description='Set the state to activate (1) or deactivate (0).',
        required=True)
})


@ns_controller.route('/<string:unique_id>')
@ns_controller.doc(
    security='apikey',
    responses=default_responses,
    params={
        'unique_id': 'The unique ID of the controller.'
    }
)
class ControllerStatus(Resource):
    """Controller status"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_controller.marshal_with(controller_status_fields)
    @flask_login.login_required
    def get(self, unique_id):
        """Get the status of a controller"""
        if not utils_general.user_has_permission('edit_controllers'):
            abort(403)

        try:
            control = DaemonControl()
            active = control.controller_is_active(unique_id)
            return {'is_active': active}, 200
        except Exception:
            abort(500, custom=traceback.format_exc())

    @accept('application/vnd.mycodo.v1+json')
    @ns_controller.expect(controller_set_fields)
    @flask_login.login_required
    def post(self, unique_id):
        """Activate or deactivate a controller"""
        if not utils_general.user_has_permission('edit_controllers'):
            abort(403)

        if 'activate' not in ns_controller.payload:
            abort(422, message='missing "activate" in payload')

        try:
            control = DaemonControl()
            if ns_controller.payload['activate']:
                activate = control.controller_activate(unique_id)
            else:
                activate = control.controller_deactivate(unique_id)
            if activate[0]:
                return {'message': activate[1]}, 460
            else:
                return {'message': activate[1]}, 200
        except Exception:
            abort(500, custom=traceback.format_exc())
