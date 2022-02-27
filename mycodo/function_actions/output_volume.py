# coding=utf-8
import threading

from flask_babel import lazy_gettext

from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import Actions
from mycodo.databases.models import Output
from mycodo.function_actions.base_function_action import AbstractFunctionAction
from mycodo.utils.constraints_pass import constraints_pass_positive_or_zero_value
from mycodo.utils.database import db_retrieve_table_daemon

FUNCTION_ACTION_INFORMATION = {
    'name_unique': 'output_volume',
    'name': '{} ({})'.format(
        TRANSLATIONS['output']['title'], TRANSLATIONS['volume']['title']),
    'library': None,
    'manufacturer': 'Mycodo',

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': lazy_gettext('Instruct the Output to dispense a volume.'),

    'usage': 'Executing <strong>self.run_action("{ACTION_ID}")</strong> will actuate a volume output. '
             'Executing <strong>self.run_action("{ACTION_ID}", value=42)</strong> will actuate a volume output with a specific volume (e.g. 42 ml).',

    'dependencies_module': [],

    'custom_options': [
        {
            'id': 'output',
            'type': 'select_measurement_channel',
            'default_value': '',
            'required': True,
            'options_select': [
                'Output_Channels_Measurements',
            ],
            'name': 'Output',
            'phrase': 'Select an output to control'
        },
        {
            'id': 'volume',
            'type': 'float',
            'default_value': 0.0,
            'required': True,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': lazy_gettext('Duty Cycle'),
            'phrase': lazy_gettext('Duty cycle for the PWM (percent, 0.0 - 100.0)')
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """
    Function Action: Output (Volume)
    """
    def __init__(self, action_dev, testing=False):
        super(ActionModule, self).__init__(action_dev, testing=testing, name=__name__)

        self.output_device_id = None
        self.output_measurement_id = None
        self.output_channel_id = None
        self.volume = None

        action = db_retrieve_table_daemon(
            Actions, unique_id=self.unique_id)
        self.setup_custom_options(
            FUNCTION_ACTION_INFORMATION['custom_options'], action)

        if not testing:
            self.setup_action()

    def setup_action(self):
        self.action_setup = True

    def run_action(self, message, dict_vars):
        values_set = False
        if "value" in dict_vars and dict_vars["value"] is not None:
            try:
                volume = dict_vars["value"]
                values_set = True
            except:
                self.logger.exception("Error setting values passed to action")

        if not values_set:
            volume = self.volume

        output_channel = self.get_output_channel_from_channel_id(
            self.output_channel_id)

        this_output = db_retrieve_table_daemon(
            Output, unique_id=self.output_device_id, entry='first')
        message += " Turn output {unique_id} CH{ch} ({id}, {name}) with volume of {vol}.".format(
            unique_id=self.output_device_id,
            ch=self.output_channel_id,
            id=this_output.id,
            name=this_output.name,
            vol=volume)

        output_on = threading.Thread(
            target=self.control.output_on,
            args=(self.output_device_id,),
            kwargs={'output_type': 'vol',
                    'amount': volume,
                    'output_channel': output_channel})
        output_on.start()

        return message

    def is_setup(self):
        return self.action_setup
