# coding=utf-8
import threading

from flask_babel import lazy_gettext

from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import Actions
from mycodo.databases.models import Output
from mycodo.actions.base_action import AbstractFunctionAction
from mycodo.utils.constraints_pass import constraints_pass_positive_or_zero_value
from mycodo.utils.database import db_retrieve_table_daemon

ACTION_INFORMATION = {
    'name_unique': 'output_on_off',
    'name': f"{TRANSLATIONS['output']['title']}: "
            f"{TRANSLATIONS['on']['title']}/{TRANSLATIONS['off']['title']}/{TRANSLATIONS['duration']['title']}",
    'library': None,
    'manufacturer': 'Mycodo',
    'application': ['functions'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': lazy_gettext('Turn an On/Off Output On, Off, or On for a duration.'),

    'usage': 'Executing <strong>self.run_action("ACTION_ID")</strong> will actuate an output. '
             'Executing <strong>self.run_action("ACTION_ID", value={"output_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b", "channel": 0, "state": "on", "duration": 300})</strong> will set the state of the output with the specified ID and channel. Don\'t forget to change the output_id value to an actual Output ID that exists in your system. If state is on and a duration is set, the output will turn off after the duration.',

    'custom_options': [
        {
            'id': 'output',
            'type': 'select_channel',
            'default_value': '',
            'required': True,
            'options_select': [
                'Output_Channels'
            ],
            'name': 'Output',
            'phrase': 'Select an output to control'
        },
        {
            'id': 'state',
            'type': 'select',
            'default_value': '',
            'required': True,
            'options_select': [
                ('on', 'On'),
                ('off', 'Off')
            ],
            'name': lazy_gettext('State'),
            'phrase': 'Turn the output on or off'
        },
        {
            'id': 'duration',
            'type': 'float',
            'default_value': 0.0,
            'required': True,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': "{} ({})".format(lazy_gettext('Duration'), lazy_gettext('Seconds')),
            'phrase': 'If On, you can set a duration to turn the output on. 0 stays on.'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """Function Action: Output (On/Off/Duration)."""
    def __init__(self, action_dev, testing=False):
        super().__init__(action_dev, testing=testing, name=__name__)

        self.output_device_id = None
        self.output_channel_id = None
        self.state = None
        self.duration = None

        action = db_retrieve_table_daemon(
            Actions, unique_id=self.unique_id)
        self.setup_custom_options(
            ACTION_INFORMATION['custom_options'], action)

        if not testing:
            self.try_initialize()

    def initialize(self):
        self.action_setup = True

    def run_action(self, dict_vars):
        try:
            output_id = dict_vars["value"]["output_id"]
        except:
            output_id = self.output_device_id

        try:
            channel = dict_vars["value"]["channel"]
        except:
            channel = self.get_output_channel_from_channel_id(
                self.output_channel_id)

        try:
            state = dict_vars["value"]["state"]
        except:
            state = self.state

        try:
            duration = dict_vars["value"]["duration"]
        except:
            duration = self.duration

        output = db_retrieve_table_daemon(
            Output, unique_id=output_id, entry='first')

        if not output:
            msg = f" Error: Output with ID '{output_id}' not found."
            dict_vars['message'] += msg
            self.logger.error(msg)
            return dict_vars

        dict_vars['message'] += f" Turn output {output_id} CH{channel} ({output.name}) {state}"

        if state == 'on' and duration:
            dict_vars['message'] += f" for {duration} seconds"
        dict_vars['message'] += "."

        output_on_off = threading.Thread(
            target=self.control.output_on_off,
            args=(output_id, state,),
            kwargs={'output_type': 'sec',
                    'amount': duration,
                    'output_channel': channel})
        output_on_off.start()

        self.logger.debug(f"Message: {dict_vars['message']}")

        return dict_vars

    def is_setup(self):
        return self.action_setup
