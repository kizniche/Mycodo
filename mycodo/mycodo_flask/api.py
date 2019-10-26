# coding=utf-8
import logging

import flask_login
from flask_restful import Resource

from mycodo.databases.models import Input
from mycodo.databases.models import User
from mycodo.databases.models.input import InputSchema
from mycodo.databases.models.user import UserSchema
from mycodo.mycodo_flask.utils import utils_general

logger = logging.getLogger(__name__)


class Inputs(Resource):
    @flask_login.login_required
    def get(self):
        if not utils_general.user_has_permission('view_settings'):
            return 'You do not have permission to access this.', 401
        inputs_list = []
        input_schema = InputSchema()
        all_inputs = Input.query.all()
        for each_input in all_inputs:
            inputs_list.append(input_schema.dump(each_input))
        return inputs_list


class Users(Resource):
    @flask_login.login_required
    def get(self):
        if not utils_general.user_has_permission('view_settings'):
            return 'You do not have permission to access this.', 401
        users_list = []
        user_schema = UserSchema()
        all_users = User.query.all()
        for each_user in all_users:
            users_list.append(user_schema.dump(each_user))
        return users_list
