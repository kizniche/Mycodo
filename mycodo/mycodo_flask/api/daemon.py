# coding=utf-8
import logging
import traceback

import flask_login
from flask_accept import accept
from flask_restx import Resource
from flask_restx import abort
from flask_restx import fields

from mycodo.mycodo_client import DaemonControl
from mycodo.mycodo_flask.api import api
from mycodo.mycodo_flask.api import default_responses
from mycodo.mycodo_flask.utils import utils_general

logger = logging.getLogger(__name__)

ns_daemon = api.namespace('daemon', description='Daemon operations')

daemon_status_fields = ns_daemon.model('Daemon Status Fields', {
    'is_running': fields.Boolean,
    'RAM': fields.Float,
    'python_virtual_env': fields.Boolean
})

daemon_terminate_fields = ns_daemon.model('Daemon Terminate Fields', {
    'terminated': fields.Boolean
})


@ns_daemon.route('/')
@ns_daemon.doc(security='apikey', responses=default_responses)
class DaemonStatus(Resource):
    """Checks information about the daemon."""

    @accept('application/vnd.mycodo.v1+json')
    @ns_daemon.marshal_with(daemon_status_fields)
    @flask_login.login_required
    def get(self):
        """Get the status of the daemon."""
        if not utils_general.user_has_permission('edit_controllers'):
            abort(403)

        try:
            control = DaemonControl()
            status = control.daemon_status()
            ram = control.ram_use()
            virtualenv = control.is_in_virtualenv()
            if status == 'alive':
                return {
                   'is_running': True,
                   'RAM': ram,
                   'python_virtual_env': virtualenv
                }, 200
        except Exception:
            return {
               'is_running': False,
               'RAM': None,
               'python_virtual_env': None
            }, 200


@ns_daemon.route('/terminate')
@ns_daemon.doc(security='apikey', responses=default_responses)
class DaemonTerminate(Resource):
    """Checks information about the daemon."""

    @accept('application/vnd.mycodo.v1+json')
    @ns_daemon.marshal_with(daemon_terminate_fields)
    @flask_login.login_required
    def post(self):
        """Shut down the daemon."""
        if not utils_general.user_has_permission('edit_controllers'):
            abort(403)

        try:
            control = DaemonControl()
            terminate = control.terminate_daemon()
            if terminate:
                return {'terminated': terminate}, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())
