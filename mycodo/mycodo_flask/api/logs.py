# coding=utf-8
import flask_login
import logging
import os
import subprocess
import traceback
from flask_accept import accept
from flask_restx import Resource
from flask_restx import abort
from flask_restx import fields

from mycodo import config
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

ns_dep = api.namespace('log', description='Log operations')


@ns_dep.route('/tail/<string:log_type>/<int:last_lines>')
@ns_dep.doc(
    security='apikey',
    responses=default_responses,
    params={'log_type': 'Log to return the last lines of. Options: login, http_access, http_error, daemon, dependency, import, keepup, backup, restore, upgrade.',
            'last_lines': 'How many lines to return.'}
)
class LogTail(Resource):
    """Tail the last lines of a log."""

    @accept('application/vnd.mycodo.v1+json')
    @flask_login.login_required
    def get(self, log_type, last_lines):
        """Tail the last lines of a log."""
        if not utils_general.user_has_permission('edit_controllers'):
            abort(403)
        try:
            if log_type == 'login':
                logfile = config.LOGIN_LOG_FILE
            elif log_type == 'http_access':
                logfile = config.HTTP_ACCESS_LOG_FILE
            elif log_type == 'http_error':
                logfile = config.HTTP_ERROR_LOG_FILE
            elif log_type == 'daemon':
                logfile = config.DAEMON_LOG_FILE
            elif log_type == 'dependency':
                logfile = config.DEPENDENCY_LOG_FILE
            elif log_type == 'import':
                logfile = config.IMPORT_LOG_FILE
            elif log_type == 'keepup':
                logfile = config.KEEPUP_LOG_FILE
            elif log_type == 'backup':
                logfile = config.BACKUP_LOG_FILE
            elif log_type == 'restore':
                logfile = config.RESTORE_LOG_FILE
            elif log_type == 'upgrade':
                logfile = config.UPGRADE_LOG_FILE
            else:
                return {'message': 'Unknown log type'}, 404

            command = None
            logrotate_file = logfile + '.1'
            if (logrotate_file and os.path.exists(logrotate_file) and
                    logfile and os.path.isfile(logfile)):
                command = f'cat {logrotate_file} {logfile} | tail -n {last_lines}'
            elif os.path.isfile(logfile):
                command = f'tail -n {last_lines} {logfile}'

            # Execute command and generate the output to display to the user
            if command:
                log = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
                (log_output, _) = log.communicate()
                log.wait()
                log_output = str(log_output, 'latin-1')
            else:
                return {'message': 'Log not found'}, 404

            return {
                'message': log_output
            }, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())
