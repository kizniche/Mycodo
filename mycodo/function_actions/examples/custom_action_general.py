# coding=utf-8
import time

from flask_babel import lazy_gettext

from mycodo.databases.models import Actions
from mycodo.function_actions.base_function_action import AbstractFunctionAction
from mycodo.utils.constraints_pass import constraints_pass_positive_value
from mycodo.utils.database import db_retrieve_table_daemon

FUNCTION_ACTION_INFORMATION = {
    'name_unique': 'custom_action_generic',
    'name': 'Custom Action: Generic',
    'library': None,
    'manufacturer': 'Mycodo',

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': 'A demo action that merely performs a calculation.',

    'usage': 'Executing <strong>self.run_action("{ACTION_ID}")</strong> will execute the calculation. '
             'Executing <strong>self.run_action("{ACTION_ID}", value={"integer_1": 24})</strong> will pass the integer value 24 to the action.',

    'dependencies_module': [],

    'custom_options': [
        {
            'id': 'controller',
            'type': 'select_device',
            'default_value': '',
            'options_select': [
                'Input',
                'Output',
                'Math',
                'Function',
                'Conditional',
                'PID',
                'Trigger'
            ],
            'name': lazy_gettext('Controller'),
            'phrase': 'Select the controller'
        },
        {
            'id': 'text_1',
            'type': 'text',
            'default_value': 'Text_1',
            'required': True,
            'name': 'Text 1',
            'phrase': 'Text 1 Description'
        },
        {
            'id': 'integer_1',
            'type': 'integer',
            'default_value': 100,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Integer 1',
            'phrase': 'Integer 1 Description'
        },
        {
            'id': 'float_1',
            'type': 'float',
            'default_value': 50.2,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Float 1',
            'phrase': 'Float 1 Description'
        },
        {
            'id': 'bool_1',
            'type': 'bool',
            'default_value': True,
            'name': 'Boolean 1',
            'phrase': 'Boolean 1 Description'
        },
        {  # This starts a new line for the next action
            'type': 'new_line'
        },
        {
            'id': 'select_1',
            'type': 'select',
            'default_value': 'SECOND',
            'options_select': [
                ('FIRST', 'First Option Selected'),
                ('SECOND', 'Second Option Selected'),
                ('THIRD', 'Third Option Selected'),
            ],
            'name': 'Select 1',
            'phrase': 'Select 1 Description'
        },
        {
            'id': 'select_measurement_1',
            'type': 'select_measurement',
            'default_value': '',
            'options_select': [
                'Input',
                'Math',
                'Function',
                'PID'
            ],
            'name': 'Select Measurement 1',
            'phrase': 'Select Measurement 1 Description'
        },
        {
            'id': 'output_1',
            'type': 'select_measurement_channel',
            'default_value': '',
            'required': True,
            'options_select': [
                'Output_Channels_Measurements',
            ],
            'name': 'Output',
            'phrase': 'Select an output to modulate that will affect the measurement'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """Function Action: Generic."""
    def __init__(self, action_dev, testing=False):
        super(ActionModule, self).__init__(action_dev, testing=testing, name=__name__)

        # Standard custom options inherit the name you defined in the "id" key
        self.text_1 = None
        self.integer_1 = None
        self.float_1 = None
        self.bool_1 = None
        self.select_1 = None

        # Custom options of type "select_measurement" require creating two variables and adding "_device_id"
        # and "_measurement_id" after the name
        self.select_measurement_1_device_id = None
        self.select_measurement_1_measurement_id = None

        # Custom options of type "select_measurement_channel" require three variables and adding
        # "device_id", "measurement_id", and "channel_id" after the name
        self.output_1_device_id = None
        self.output_1_measurement_id = None
        self.output_1_channel_id = None

        # Custom options of type "select_device" require adding "_id" after the name
        self.controller_id = None

        # Set custom options
        action = db_retrieve_table_daemon(
            Actions, unique_id=self.unique_id)
        self.setup_custom_options(
            FUNCTION_ACTION_INFORMATION['custom_options'], action)

        if not testing:
            self.setup_action()

    def setup_action(self):
        # Place imports here, if applicable
        # Often derived from dependencies_module, above
        self.action_setup = True

    def run_action(self, message, dict_vars):
        try:
            integer_1 = int(dict_vars["value"]["integer_1"])
        except:
            integer_1 = self.integer_1

        # These log lines will appear in teh Daemon Log.
        # Logs can be viewed at Config -> Mycodo Logs -> Damon Log.
        self.logger.info(
            "Custom controller started with options: "
            "{}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}".format(
                self.text_1,
                integer_1,
                self.float_1,
                self.bool_1,
                self.select_1,
                self.select_measurement_1_device_id,
                self.select_measurement_1_measurement_id,
                self.output_1_device_id,
                self.output_1_measurement_id,
                self.output_1_channel_id,
                self.controller_id))

        self.logger.info("dict_vars = {}".format(dict_vars))

        if not integer_1:
            msg = " Error: integer_1 not set. Cannot calculate the time."
            message += msg
            self.logger.error(msg)
            return message

        now = int(time.time())

        message += " The current epoch time is {time}. The epoch {hr} hour{plural} in the future is {epoch}.".format(
            time=now,
            hr=integer_1,
            plural="s" if integer_1 > 1 else "",
            epoch=now + (integer_1 * 60 * 60))

        self.logger.info("Message: {}".format(message))

        return message

    def is_setup(self):
        return self.action_setup
