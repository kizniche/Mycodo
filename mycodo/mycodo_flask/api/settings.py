# coding=utf-8
import logging

import flask_login
from flask_restplus import Namespace
from flask_restplus import Resource

from mycodo.databases.models import Input
from mycodo.databases.models import Output
from mycodo.databases.models import User
from mycodo.databases.models.input import InputSchema
from mycodo.databases.models.output import OutputSchema
from mycodo.databases.models.user import UserSchema
from mycodo.mycodo_flask.utils import utils_general

logger = logging.getLogger(__name__)

ns_settings = Namespace('settings', description='Settings operations')


@ns_settings.route('/input/<string:uuid>')
@ns_settings.doc(params={'uuid': 'The Unique ID'})
class InputSingle(Resource):
    """Interacts with Input settings in the SQL database"""
    @ns_settings.doc(
        security='apikey',
        responses={
            200: 'Success',
            401: 'Invalid API Key',
            403: 'Insufficient Permissions',
            404: 'Not Found',
        }
    )
    @flask_login.login_required
    def get(self, uuid):
        """Shows the Input settings for an input with the specified uuid"""
        if not utils_general.user_has_permission('view_settings'):
            return 'You do not have permission to access this.', 401
        input_schema = InputSchema()
        input_ = Input.query.filter_by(unique_id=uuid).first()
        return input_schema.dump(input_)


@ns_settings.route('/inputs')
class InputDump(Resource):
    """Interacts with Input settings in the SQL database"""
    @ns_settings.doc(
        security='apikey',
        responses={
            200: 'Success',
            401: 'Invalid API Key',
            403: 'Insufficient Permissions',
            404: 'Not Found',
        }
    )
    @flask_login.login_required
    def get(self):
        """Shows all Input settings"""
        if not utils_general.user_has_permission('view_settings'):
            return 'You do not have permission to access this.', 401
        input_schema = InputSchema()
        return input_schema.dump(Input.query.all(), many=True)


@ns_settings.route('/output/<string:uuid>')
@ns_settings.doc(params={'uuid': 'The Unique ID'})
class OutputSingle(Resource):
    """Interacts with Output settings in the SQL database"""
    @ns_settings.doc(
        security='apikey',
        responses={
            200: 'Success',
            401: 'Invalid API Key',
            403: 'Insufficient Permissions',
            404: 'Not Found',
        }
    )
    @flask_login.login_required
    def get(self, uuid):
        """Shows the Output settings for an output with the specified uuid"""
        if not utils_general.user_has_permission('view_settings'):
            return 'You do not have permission to access this.', 401
        output_schema = OutputSchema()
        output_ = Output.query.filter_by(unique_id=uuid).first()
        return output_schema.dump(output_)


@ns_settings.route('/outputs')
class outputDump(Resource):
    """Interacts with output settings in the SQL database"""
    @ns_settings.doc(
        security='apikey',
        responses={
            200: 'Success',
            401: 'Invalid API Key',
            403: 'Insufficient Permissions',
            404: 'Not Found',
        }
    )
    @flask_login.login_required
    def get(self):
        """Shows all output settings"""
        if not utils_general.user_has_permission('view_settings'):
            return 'You do not have permission to access this.', 401
        output_schema = OutputSchema()
        return output_schema.dump(Output.query.all(), many=True)


@ns_settings.route('/user/<string:uuid>')
@ns_settings.doc(params={'uuid': 'The Unique ID'})
class UserSingle(Resource):
    """Interacts with User settings in the SQL database"""
    @ns_settings.doc(
        security='apikey',
        responses={
            200: 'Success',
            401: 'Invalid API Key',
            403: 'Insufficient Permissions',
            404: 'Not Found',
        }
    )
    @flask_login.login_required
    def get(self, uuid):
        """Shows the User settings for an user with the specified uuid"""
        if not utils_general.user_has_permission('view_settings'):
            return 'You do not have permission to access this.', 401
        user_schema = UserSchema()
        user_ = User.query.filter_by(unique_id=uuid).first()
        return user_schema.dump(user_)


@ns_settings.route('/users')
class UserDump(Resource):
    """Interacts with User settings in the SQL database"""
    @ns_settings.doc(
        security='apikey',
        responses={
            200: 'Success',
            401: 'Invalid API Key',
            403: 'Insufficient Permissions',
            404: 'Not Found',
        }
    )
    @flask_login.login_required
    def get(self):
        """Shows all User settings"""
        if not utils_general.user_has_permission('view_settings'):
            return 'You do not have permission to access this.', 401
        user_schema = UserSchema()
        return user_schema.dump(User.query.all(), many=True)
