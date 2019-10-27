# coding=utf-8
from flask import Blueprint
from flask_restplus import Api

from mycodo.mycodo_flask.api.output import ns_output
from mycodo.mycodo_flask.api.settings import ns_settings

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
