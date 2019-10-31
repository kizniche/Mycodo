# coding=utf-8
import logging
import traceback

import flask_login
from flask_accept import accept
from flask_restplus import Namespace
from flask_restplus import Resource
from flask_restplus import abort
from flask_restplus import fields

from mycodo.databases.models import User
from mycodo.databases.models.user import UserSchema
from mycodo.mycodo_flask.utils import utils_general

logger = logging.getLogger(__name__)

ns_user = Namespace('users', description='User operations')

default_responses = {
    200: 'Success',
    401: 'Invalid API Key',
    403: 'Insufficient Permissions',
    404: 'Not Found',
    429: 'Too Many Requests',
    500: 'Internal Server Error'
}

user_fields = ns_user.model('User Settings Fields', {
    "id": fields.Integer,
    "unique_id": fields.String,
    "name": fields.String,
    "email": fields.String,
    "role_id": fields.Integer,
    "theme": fields.String,
    "landing_page": fields.String,
    "language": fields.String
})

user_list_fields = ns_user.model('User Settings Fields List', {
    'users': fields.List(fields.Nested(user_fields)),
})


@ns_user.route('/')
@ns_user.doc(security='apikey', responses=default_responses)
class UserDump(Resource):
    """Interacts with User settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_user.marshal_with(user_list_fields)
    @flask_login.login_required
    def get(self):
        """Show all user settings"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            user_schema = UserSchema()
            user_data = user_schema.dump(User.query.all(), many=True)
            if user_data:
                return {'users': user_data[0]}, 200
        except Exception:
            abort(500, custom=traceback.format_exc())


@ns_user.route('/by_unique_id/<string:unique_id>')
@ns_user.doc(
    security='apikey',
    responses=default_responses,
    params={'unique_id': 'The unique ID of the user'}
)
class UserSingle(Resource):
    """Interacts with user settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_user.marshal_with(user_fields)
    @flask_login.login_required
    def get(self, unique_id):
        """Show the settings for a user with the unique_id"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            user_schema = UserSchema()
            user_data = user_schema.dump(
                User.query.filter_by(unique_id=unique_id).first())
            if user_data:
                return user_data[0], 200
        except Exception:
            abort(500, custom=traceback.format_exc())
