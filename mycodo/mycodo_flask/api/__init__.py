# coding=utf-8
import logging

from flask import Blueprint
from flask_restplus import Api

from mycodo.mycodo_flask.api.output import ns_output
from mycodo.mycodo_flask.api.settings import ns_settings

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__, url_prefix='/api')

authorizations = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'X-API-KEY'
    }
}

api = Api(
    api_bp,
    version='1.0',
    title='Mycodo API',
    description='An API for Mycodo',
    authorizations=authorizations
)

api.add_namespace(ns_output)
api.add_namespace(ns_settings)


# import flask_login
# from flask_restplus import Resource
# @api.route('/export_swagger')
# @api.doc(security='apikey')
# class ExportSwaggerJSON(Resource):
#     """Exports swagger JSON"""
#     @flask_login.login_required
#     def get(self):
#         """Export swagger JSON to swagger.json file"""
#         from mycodo.mycodo_flask.utils import utils_general
#         import json
#         if not utils_general.user_has_permission('view_settings'):
#             return 'You do not have permission to access this.', 401
#         with open("/home/pi/swagger.json", "w") as text_file:
#             text_file.write(json.dumps(api.__schema__, indent=2))
