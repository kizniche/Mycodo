# coding=utf-8
from flask_babel import lazy_gettext

from mycodo.actions.base_action import AbstractFunctionAction
from mycodo.databases.models import Actions
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.system_pi import get_measurement

ACTION_INFORMATION = {
    'name_unique': 'example_action_input',
    'name': 'Example Action: For Input',
    'library': None,
    'manufacturer': 'Mycodo',

    # Define which controller(s) the Action can be applied to.
    'application': ['inputs'],  # Options: functions, inputs

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': 'An example action for Inputs that merely performs a calculation from the Input measurement.',

    'usage': 'Executing <strong>self.run_action("ACTION_ID")</strong> will execute the calculation. '
             'Executing <strong>self.run_action("ACTION_ID", value={"integer_1": 24})</strong> will pass the integer value 24 to the action.',

    'dependencies_module': [],

    'custom_options': [
        {
            'id': 'measurement',
            'type': 'select_measurement_from_this_input',
            'default_value': None,
            'name': lazy_gettext('Measurement'),
            'phrase': 'Select the measurement to send as the payload'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """Function Action: Generic."""
    def __init__(self, action_dev, testing=False):
        super().__init__(action_dev, testing=testing, name=__name__)

        # Standard custom options inherit the name you defined in the "id" key
        self.measurement_device_id = None
        self.measurement_measurement_id = None

        # Set custom options
        action = db_retrieve_table_daemon(
            Actions, unique_id=self.unique_id)
        self.setup_custom_options(
            ACTION_INFORMATION['custom_options'], action)

        if not testing:
            self.try_initialize()

    def initialize(self):
        # Place imports here, if applicable
        # Often derived from dependencies_module, above
        self.action_setup = True

    def run_action(self, message, dict_vars):
        device_measurement = get_measurement(
            self.measurement_measurement_id)
        if not device_measurement:
            msg = f" Error: A measurement needs to be selected."
            self.logger.error(msg)
            message += msg
            return message

        channel = device_measurement.channel

        try:
            measurement = dict_vars["value"][channel]['value']
        except:
            measurement = None

        self.logger.debug(f"Input channel: {channel}, measurement: {measurement}")

        if measurement is None:
            msg = f" Error: No measurement found in dictionary passed to Action for channel {channel}."
            self.logger.error(msg)
            message += msg
            return message

        message += f" Measurement from Input is {measurement}. Do what you want with it in this Action module."

        self.logger.info(f"Message: {message}")

        return message

    def is_setup(self):
        return self.action_setup
