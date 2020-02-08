# coding=utf-8
import logging
import traceback

import flask_login
from flask_accept import accept
from flask_restx import Resource
from flask_restx import abort
from flask_restx import fields

from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import Math
from mycodo.databases.models.math import MathSchema
from mycodo.databases.models.measurement import DeviceMeasurementsSchema
from mycodo.mycodo_flask.api import api
from mycodo.mycodo_flask.api import default_responses
from mycodo.mycodo_flask.api.sql_schema_fields import device_measurement_fields
from mycodo.mycodo_flask.api.sql_schema_fields import math_fields
from mycodo.mycodo_flask.api.utils import get_from_db
from mycodo.mycodo_flask.api.utils import return_list_of_dictionaries
from mycodo.mycodo_flask.utils import utils_general

logger = logging.getLogger(__name__)

ns_math = api.namespace('maths', description='Math operations')

math_single_fields = api.model('Math Status Fields', {
    'math settings': fields.Nested(math_fields),
    'device measurements': fields.List(
        fields.Nested(device_measurement_fields)),
})

math_list_fields = api.model('Math Fields List', {
    'math settings': fields.List(fields.Nested(math_fields)),
})


@ns_math.route('/')
@ns_math.doc(security='apikey', responses=default_responses)
class Maths(Resource):
    """Math information"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_math.marshal_with(math_list_fields)
    @flask_login.login_required
    def get(self):
        """Show all math settings"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            list_data = get_from_db(MathSchema, Math)
            if list_data:
                return {'math settings': list_data}, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_math.route('/<string:unique_id>')
@ns_math.doc(
    security='apikey',
    responses=default_responses,
    params={'unique_id': 'The unique ID of the math'}
)
class SettingsMathsUniqueID(Resource):
    """Interacts with math settings in the SQL database"""

    @accept('application/vnd.mycodo.v1+json')
    @ns_math.marshal_with(math_single_fields)
    @flask_login.login_required
    def get(self, unique_id):
        """Show the settings for a math"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            dict_data = get_from_db(MathSchema, Math, unique_id=unique_id)

            measure_schema = DeviceMeasurementsSchema()
            list_data = return_list_of_dictionaries(
                measure_schema.dump(
                    DeviceMeasurements.query.filter_by(
                        device_id=unique_id).all(), many=True))

            return {'math settings': dict_data,
                    'device measurements': list_data}, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())
