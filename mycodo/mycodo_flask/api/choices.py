# coding=utf-8
import logging
import traceback

import flask_login
from flask_accept import accept
from flask_restplus import Namespace
from flask_restplus import Resource
from flask_restplus import abort

from mycodo.databases.models import Input
from mycodo.databases.models import Measurement
from mycodo.databases.models import Output
from mycodo.databases.models import PID
from mycodo.databases.models import Unit
from mycodo.mycodo_flask.utils import utils_general
from mycodo.utils.system_pi import add_custom_measurements
from mycodo.utils.system_pi import add_custom_units

logger = logging.getLogger(__name__)

ns_choices_measurement = Namespace(
    'choices', description='Form choice operations')

default_responses = {
    200: 'Success',
    401: 'Invalid API Key',
    403: 'Insufficient Permissions',
    404: 'Not Found',
    422: 'Unprocessable Entity',
    429: 'Too Many Requests',
    500: 'Internal Server Error'
}


@ns_choices_measurement.route('/controllers/')
@ns_choices_measurement.doc(security='apikey', responses=default_responses)
class ChoicesInputs(Resource):
    """Form choices for controllers"""

    @accept('application/vnd.mycodo.v1+json')
    @flask_login.login_required
    def get(self):
        """Show form choices for all controllers"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            input_choices = utils_general.choices_controller_ids()

            if input_choices:
                return {'choices controllers': input_choices}, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_choices_measurement.route('/input/measurements/')
@ns_choices_measurement.doc(security='apikey', responses=default_responses)
class ChoicesInputs(Resource):
    """Form choices for input measurements"""

    @accept('application/vnd.mycodo.v1+json')
    @flask_login.login_required
    def get(self):
        """Show form choices for all input measurements"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            input_dev = Input.query.all()
            dict_measurements = add_custom_measurements(Measurement.query.all())
            dict_units = add_custom_units(Unit.query.all())
            input_choices = utils_general.choices_inputs(
                input_dev, dict_units, dict_measurements)

            if input_choices:
                return {'choices input measurements': input_choices}, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_choices_measurement.route('/output/devices/')
@ns_choices_measurement.doc(security='apikey', responses=default_responses)
class ChoicesOutputDevices(Resource):
    """Form choices for output devices"""

    @accept('application/vnd.mycodo.v1+json')
    @flask_login.login_required
    def get(self):
        """Show form choices for all output devices"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            output = Output.query.all()
            dict_measurements = add_custom_measurements(Measurement.query.all())
            dict_units = add_custom_units(Unit.query.all())
            output_choices = utils_general.choices_output_devices(
                output, dict_units, dict_measurements)

            if output_choices:
                return {'choices output devices': output_choices}, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_choices_measurement.route('/output/measurements/')
@ns_choices_measurement.doc(security='apikey', responses=default_responses)
class ChoicesOutputMeasurements(Resource):
    """Form choices for output measurements"""

    @accept('application/vnd.mycodo.v1+json')
    @flask_login.login_required
    def get(self):
        """Show form choices for all output measurements"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            output = Output.query.all()
            dict_measurements = add_custom_measurements(Measurement.query.all())
            dict_units = add_custom_units(Unit.query.all())
            output_choices = utils_general.choices_outputs(
                output, dict_units, dict_measurements)

            if output_choices:
                return {'choices output measurements': output_choices}, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_choices_measurement.route('/pid/measurements/')
@ns_choices_measurement.doc(security='apikey', responses=default_responses)
class ChoicesPIDs(Resource):
    """Form choices for pid measurements"""

    @accept('application/vnd.mycodo.v1+json')
    @flask_login.login_required
    def get(self):
        """Show form choices for all PID measurements"""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            pid = PID.query.all()
            dict_measurements = add_custom_measurements(Measurement.query.all())
            dict_units = add_custom_units(Unit.query.all())
            pid_choices = utils_general.choices_pids(
                pid, dict_units, dict_measurements)

            if pid_choices:
                return {'choices pid measurements': pid_choices}, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())
