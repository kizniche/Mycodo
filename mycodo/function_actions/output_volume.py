# coding=utf-8
import threading

from flask_babel import lazy_gettext

from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import Actions
from mycodo.databases.models import Output
from mycodo.function_actions.base_function_action import AbstractFunctionAction
from mycodo.utils.constraints_pass import constraints_pass_positive_value
from mycodo.utils.database import db_retrieve_table_daemon

FUNCTION_ACTION_INFORMATION = {
    'name_unique': 'output_volume',
    'name': '{}: {}'.format(
        TRANSLATIONS['output']['title'],
        TRANSLATIONS['volume']['title']),
    'library': None,
    'manufacturer': 'Mycodo',

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': lazy_gettext('Instruct the Output to dispense a volume.'),

    'usage': 'Executing <strong>self.run_action("{ACTION_ID}")</strong> will actuate a volume output. '
             'Executing <strong>self.run_action("{ACTION_ID}", value={"output_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b", "channel": 0, "volume": 42})</strong> will send a volume to the output with the specified ID and channel.',

    'dependencies_module': [],

    'custom_options': [
        {
            'id': 'output',
            'type': 'select_channel',
            'default_value': '',
            'required': True,
            'options_select': [
                'Output_Channels',
            ],
            'name': 'Output',
            'phrase': 'Select an output to control'
        },
        {
            'id': 'volume',
            'type': 'float',
            'default_value': 0.0,
            'required': False,
            'constraints_pass': constraints_pass_positive_value,
            'name': lazy_gettext('Volume'),
            'phrase': 'The volume to send to the output'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """Function Action: Output (Volume)."""
    def __init__(self, action_dev, testing=False):
        super(ActionModule, self).__init__(action_dev, testing=testing, name=__name__)

        self.output_device_id = None
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
        try:
            output_id = dict_vars["value"]["output_id"]
        except:
            output_id = self.output_device_id

        try:
            output_channel = dict_vars["value"]["channel"]
        except:
            output_channel = self.get_output_channel_from_channel_id(
                self.output_channel_id)

        try:
            volume = dict_vars["value"]["volume"]
        except:
            volume = self.volume

        this_output = db_retrieve_table_daemon(
            Output, unique_id=output_id, entry='first')

        if not this_output:
            msg = " Error: Output with ID '{}' not found.".format(this_output)
            message += msg
            self.logger.error(msg)
            return message

        message += " Turn output {unique_id} CH{ch} ({id}, {name}) with volume of {vol}.".format(
            unique_id=output_id,
            ch=output_channel,
            id=this_output.id,
            name=this_output.name,
            vol=volume)

        output_on = threading.Thread(
            target=self.control.output_on,
            args=(output_id,),
            kwargs={'output_type': 'vol',
                    'amount': volume,
                    'output_channel': output_channel})
        output_on.start()

        self.logger.debug("Message: {}".format(message))

        return message

    def is_setup(self):
        return self.action_setup
