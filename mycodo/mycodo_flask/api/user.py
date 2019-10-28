# coding=utf-8
import logging
import traceback

import flask_login
from flask_restplus import Namespace
from flask_restplus import Resource

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
    460: 'Fail',
    461: 'Unknown Response'
}


@ns_user.route('/')
@ns_user.doc(security='apikey', responses=default_responses)
class UserDump(Resource):
    """Interacts with User settings in the SQL database"""
    @flask_login.login_required
    def get(self):
        """Show all user settings"""
        if not utils_general.user_has_permission('view_settings'):
            return 'You do not have permission to access this.', 401
        try:
            user_schema = UserSchema()
            return user_schema.dump(User.query.all(), many=True)[0], 200
        except Exception:
            return 'Fail: {}'.format(traceback.format_exc()), 460


@ns_user.route('/<string:unique_id>')
@ns_user.doc(security='apikey', responses=default_responses)
@ns_user.doc(params={'unique_id': 'The unique ID of the user'})
class UserSingle(Resource):
    """Interacts with user settings in the SQL database"""
    @flask_login.login_required
    def get(self, unique_id):
        """Show the settings for a user"""
        if not utils_general.user_has_permission('view_settings'):
            return 'You do not have permission to access this.', 401
        try:
            user_schema = UserSchema()
            user_ = User.query.filter_by(unique_id=unique_id).first()
            return user_schema.dump(user_), 200
        except Exception:
            return 'Fail: {}'.format(traceback.format_exc()), 460
