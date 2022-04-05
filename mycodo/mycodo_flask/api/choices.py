# coding=utf-8
import logging
import traceback

import flask_login
from flask_accept import accept
from flask_restx import Resource
from flask_restx import abort
from flask_restx import fields

from mycodo.databases.models import Input
from mycodo.databases.models import Measurement
from mycodo.databases.models import Output
from mycodo.databases.models import OutputChannel
from mycodo.databases.models import PID
from mycodo.databases.models import Unit
from mycodo.mycodo_flask.api import api
from mycodo.mycodo_flask.api import default_responses
from mycodo.mycodo_flask.utils import utils_general
from mycodo.utils.outputs import parse_output_information
from mycodo.utils.system_pi import add_custom_measurements
from mycodo.utils.system_pi import add_custom_units

logger = logging.getLogger(__name__)

ns_choices = api.namespace(
    'choices', description='Form choice operations')

choices_item_value_fields = ns_choices.model('Choices Controller Fields', {
    'item': fields.String,
    'value': fields.String
})

choices_controllers_list_fields = ns_choices.model(
    'Choices Controller Fields List', {
        'choices controllers': fields.List(
            fields.Nested(choices_item_value_fields)),
    }
)

choices_inputs_measurements_list_fields = ns_choices.model(
    'Choices Inputs Measurements Fields List', {
        'choices inputs measurements': fields.List(
            fields.Nested(choices_item_value_fields)),
    }
)

choices_outputs_measurements_list_fields = ns_choices.model(
    'Choices Outputs Measurements Fields List', {
        'choices outputs measurements': fields.List(
            fields.Nested(choices_item_value_fields)),
    }
)

choices_outputs_device_measurements_list_fields = ns_choices.model(
    'Choices Outputs Device Measurements Fields List', {
        'choices outputs devices': fields.List(
            fields.Nested(choices_item_value_fields)),
    }
)

choices_pids_measurements_list_fields = ns_choices.model(
    'Choices PIDs Measurements Fields List', {
        'choices pids measurements': fields.List(
            fields.Nested(choices_item_value_fields)),
    }
)


@ns_choices.route('/controllers')
@ns_choices.doc(security='apikey', responses=default_responses)
class ChoicesControllers(Resource):
    """Form choices for controllers."""

    @accept('application/vnd.mycodo.v1+json')
    @ns_choices.marshal_with(choices_controllers_list_fields)
    @flask_login.login_required
    def get(self):
        """Show form choices for all controllers."""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            choices_controllers = utils_general.choices_controller_ids()
            return {'choices controllers': choices_controllers}, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_choices.route('/inputs/measurements')
@ns_choices.doc(security='apikey', responses=default_responses)
class ChoicesInputMeasurements(Resource):
    """Form choices for input measurements."""

    @accept('application/vnd.mycodo.v1+json')
    @ns_choices.marshal_with(choices_inputs_measurements_list_fields)
    @flask_login.login_required
    def get(self):
        """Show form choices for all input measurements."""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            input_dev = Input.query.all()
            dict_measurements = add_custom_measurements(
                Measurement.query.all())
            dict_units = add_custom_units(Unit.query.all())
            input_choices = utils_general.choices_inputs(
                input_dev, dict_units, dict_measurements)

            if input_choices:
                return {'choices inputs measurements': input_choices}, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_choices.route('/outputs/devices')
@ns_choices.doc(security='apikey', responses=default_responses)
class ChoicesOutputDevices(Resource):
    """Form choices for output devices."""

    @accept('application/vnd.mycodo.v1+json')
    @ns_choices.marshal_with(choices_outputs_device_measurements_list_fields)
    @flask_login.login_required
    def get(self):
        """Show form choices for all output devices."""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            choices_output_devices = utils_general.choices_output_devices(
                Output.query.all())
            return {'choices outputs devices': choices_output_devices}, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_choices.route('/outputs/measurements')
@ns_choices.doc(security='apikey', responses=default_responses)
class ChoicesOutputMeasurements(Resource):
    """Form choices for output measurements."""

    @accept('application/vnd.mycodo.v1+json')
    @ns_choices.marshal_with(choices_outputs_measurements_list_fields)
    @flask_login.login_required
    def get(self):
        """Show form choices for all output measurements."""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            output = Output.query.all()
            dict_outputs = parse_output_information()
            dict_measurements = add_custom_measurements(
                Measurement.query.all())
            dict_units = add_custom_units(Unit.query.all())
            output_choices = utils_general.choices_outputs(
                output, OutputChannel, dict_outputs, dict_units, dict_measurements)

            if output_choices:
                return {'choices outputs measurements': output_choices}, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_choices.route('/pids/measurements')
@ns_choices.doc(security='apikey', responses=default_responses)
class ChoicesPIDs(Resource):
    """Form choices for pid measurements."""

    @accept('application/vnd.mycodo.v1+json')
    @ns_choices.marshal_with(choices_pids_measurements_list_fields)
    @flask_login.login_required
    def get(self):
        """Show form choices for all PID measurements."""
        if not utils_general.user_has_permission('view_settings'):
            abort(403)
        try:
            pid = PID.query.all()
            dict_measurements = add_custom_measurements(
                Measurement.query.all())
            dict_units = add_custom_units(Unit.query.all())
            pid_choices = utils_general.choices_pids(
                pid, dict_units, dict_measurements)

            if pid_choices:
                return {'choices pids measurements': pid_choices}, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())
