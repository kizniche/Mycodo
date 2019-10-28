# coding=utf-8
import logging
import traceback

import flask_login
from flask_restplus import Namespace
from flask_restplus import Resource

from mycodo.databases.models import Input
from mycodo.databases.models.input import InputSchema
from mycodo.mycodo_flask.utils import utils_general

logger = logging.getLogger(__name__)

ns_input = Namespace('input', description='Input operations')

default_responses = {
    200: 'Success',
    401: 'Invalid API Key',
    403: 'Insufficient Permissions',
    404: 'Not Found',
    429: 'Too Many Requests',
    460: 'Fail',
    461: 'Unknown Response'
}


@ns_input.route('/settings/<string:unique_id>')
@ns_input.doc(security='apikey', responses=default_responses)
@ns_input.doc(params={'unique_id': 'The unique ID of the input'})
class InputSingle(Resource):
    """Interacts with Input settings in the SQL database"""
    @flask_login.login_required
    def get(self, unique_id):
        """Show the settings for an input"""
        if not utils_general.user_has_permission('view_settings'):
            return 'You do not have permission to access this.', 401
        try:
            input_schema = InputSchema()
            input_ = Input.query.filter_by(unique_id=unique_id).first()
            return input_schema.dump(input_), 200
        except Exception:
            return 'Fail: {}'.format(traceback.format_exc()), 460


@ns_input.route('/settings_all')
@ns_input.doc(security='apikey', responses=default_responses)
class InputDump(Resource):
    """Interacts with Input settings in the SQL database"""
    @flask_login.login_required
    def get(self):
        """Show all input settings"""
        if not utils_general.user_has_permission('view_settings'):
            return 'You do not have permission to access this.', 401
        try:
            input_schema = InputSchema()
            return input_schema.dump(Input.query.all(), many=True)[0], 200
        except Exception:
            return 'Fail: {}'.format(traceback.format_exc()), 460

