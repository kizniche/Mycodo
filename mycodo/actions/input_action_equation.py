# coding=utf-8
from flask_babel import lazy_gettext

from mycodo.actions.base_action import AbstractFunctionAction
from mycodo.databases.models import Actions
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.system_pi import get_measurement

ACTION_INFORMATION = {
    'name_unique': 'input_action_equation',
    'name': "{} (Single-Measurement)".format(lazy_gettext('Equation')),
    'library': None,
    'manufacturer': 'Mycodo',
    'application': ['inputs'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': 'Modify a channel value with an equation before storing it in the database.',

    'usage': '',

    'custom_options': [
        {
            'id': 'measurement',
            'type': 'select_measurement_from_this_input',
            'default_value': None,
            'name': lazy_gettext('Measurement'),
            'phrase': 'Select the measurement to send as the payload'
        },
        {
            'id': 'equation',
            'type': 'text',
            'default_value': 'x-10',
            'required': True,
            'name': lazy_gettext('Equation'),
            'phrase': 'The equation to apply to the value before storing. "x" is the measurement value. Example: x-10'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """Function Action: Equation."""
    def __init__(self, action_dev, testing=False):
        super().__init__(action_dev, testing=testing, name=__name__)

        self.measurement_device_id = None
        self.measurement_measurement_id = None
        self.equation = None

        action = db_retrieve_table_daemon(
            Actions, unique_id=self.unique_id)
        self.setup_custom_options(
            ACTION_INFORMATION['custom_options'], action)

        if not testing:
            self.try_initialize()

    def initialize(self):
        self.action_setup = True

    def run_action(self, dict_vars):
        device_measurement = get_measurement(
            self.measurement_measurement_id)

        if not device_measurement:
            msg = f" Error: A measurement needs to be selected as the payload."
            self.logger.error(msg)
            dict_vars['message'] += msg
            return dict_vars

        channel = device_measurement.channel

        try:
            original_value = dict_vars['measurements_dict'][channel]['value']
        except:
            original_value = None

        if original_value is None:
            msg = f" Error: No measurement found in dictionary passed to Action for channel {channel}."
            self.logger.debug(msg)
            dict_vars['message'] += msg
            return dict_vars

        equation_str = self.equation
        equation_str = equation_str.replace("x", str(original_value))

        self.logger.debug("Equation: {} = {}".format(self.equation, equation_str))

        dict_vars['measurements_dict'][channel]['value'] = eval(equation_str)

        self.logger.debug(
            f"Input channel: {channel}, "
            f"original value: {original_value}, "
            f"returned value: {dict_vars['measurements_dict'][channel]['value']}")

        dict_vars['message'] += f" Equation '{equation_str}', return value = {dict_vars['measurements_dict'][channel]['value']}."

        return dict_vars

    def is_setup(self):
        return self.action_setup
