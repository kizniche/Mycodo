# coding=utf-8
import logging

from flask import Blueprint
from flask_restplus import Api

from mycodo.mycodo_flask.api.v1.input import ns_input
from mycodo.mycodo_flask.api.v1.measurement import ns_measurement
from mycodo.mycodo_flask.api.v1.output import ns_output
from mycodo.mycodo_flask.api.v1.pid import ns_pid
from mycodo.mycodo_flask.api.v1.user import ns_user

logger = logging.getLogger(__name__)

api_v1_blueprint = Blueprint('api_v1', __name__, url_prefix='/api/v1')

authorizations = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'X-API-KEY'
    }
}

api_v1 = Api(
    api_v1_blueprint,
    version='1.0',
    title='Mycodo API',
    description='An API for Mycodo',
    authorizations=authorizations
)

api_v1.add_namespace(ns_input)
api_v1.add_namespace(ns_measurement)
api_v1.add_namespace(ns_output)
api_v1.add_namespace(ns_pid)
api_v1.add_namespace(ns_user)
