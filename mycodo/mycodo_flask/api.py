# coding=utf-8
import logging

import flask_login
from flask import Blueprint
from flask_restplus import Api
from flask_restplus import Resource

from mycodo.databases.models import Input
from mycodo.databases.models import User
from mycodo.databases.models.input import InputSchema
from mycodo.databases.models.user import UserSchema
from mycodo.mycodo_flask.utils import utils_general

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__, url_prefix='/api')

api = Api(api_bp, version='1.0', title='Mycodo API',
          description='An API for Mycodo')


@api.route('/inputs')
class Users(Resource):
    """Interacts with Input settings in the SQL database"""
    @api.doc('dump_users')
    @flask_login.login_required
    def get(self):
        """Dumps all Input settings"""
        if not utils_general.user_has_permission('view_settings'):
            return 'You do not have permission to access this.', 401
        input_schema = InputSchema()
        return input_schema.dump(Input.query.all(), many=True)


@api.route('/users')
class Users(Resource):
    """Interacts with User settings in the SQL database"""
    @api.doc('dump_users')
    @flask_login.login_required
    def get(self):
        """Dumps all User settings"""
        if not utils_general.user_has_permission('view_settings'):
            return 'You do not have permission to access this.', 401
        user_schema = UserSchema()
        return user_schema.dump(User.query.all(), many=True)
