# coding=utf-8
import threading
import time

from flask_babel import lazy_gettext

from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import Actions
from mycodo.databases.models import Output
from mycodo.actions.base_action import AbstractFunctionAction
from mycodo.utils.constraints_pass import constraints_pass_positive_or_zero_value
from mycodo.utils.constraints_pass import constraints_pass_positive_value
from mycodo.utils.database import db_retrieve_table_daemon

ACTION_INFORMATION = {
    'name_unique': 'output_ramp_pwm',
    'name': f"{TRANSLATIONS['output']['title']}: {TRANSLATIONS['ramp']['title']} {TRANSLATIONS['duty_cycle']['title']}",
    'library': None,
    'manufacturer': 'Mycodo',
    'application': ['functions'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': lazy_gettext('Ramp a PWM Output from one duty cycle to another duty cycle over a period of time.'),

    'usage': 'Executing <strong>self.run_action("ACTION_ID")</strong> will ramp the PWM output duty cycle according to the settings. '
             'Executing <strong>self.run_action("ACTION_ID", value={"output_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b", "channel": 0, "start": 42, "end": 62, "increment": 1.0, "duration": 600})</strong> will ramp the duty cycle of the PWM output with the specified ID and channel. Don\'t forget to change the output_id value to an actual Output ID that exists in your system.',

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
            'id': 'start',
            'type': 'float',
            'default_value': 0.0,
            'required': True,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': "{}: {}".format(lazy_gettext('Duty Cycle'), lazy_gettext('Start')),
            'phrase': lazy_gettext('Duty cycle for the PWM (percent, 0.0 - 100.0)')
        },
        {
            'id': 'end',
            'type': 'float',
            'default_value': 50.0,
            'required': True,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': "{}: {}".format(lazy_gettext('Duty Cycle'), lazy_gettext('End')),
            'phrase': lazy_gettext('Duty cycle for the PWM (percent, 0.0 - 100.0)')
        },
        {
            'id': 'increment',
            'type': 'float',
            'default_value': 1.0,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': "{} ({})".format(lazy_gettext('Increment'), lazy_gettext('Duty Cycle')),
            'phrase': 'How much to change the duty cycle every Duration'
        },
        {
            'id': 'duration',
            'type': 'float',
            'default_value': 0.0,
            'required': True,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': "{} ({})".format(lazy_gettext('Duration'), lazy_gettext('Seconds')),
            'phrase': 'How long to ramp from start to finish.'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """Function Action: Output (On/Off/Duration)."""
    def __init__(self, action_dev, testing=False):
        super().__init__(action_dev, testing=testing, name=__name__)

        self.output_device_id = None
        self.output_channel_id = None
        self.start = None
        self.end = None
        self.increment = None
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
            start = dict_vars["value"]["start"]
        except:
            start = self.start

        try:
            end = dict_vars["value"]["end"]
        except:
            end = self.end

        try:
            increment = dict_vars["value"]["increment"]
        except:
            increment = self.increment

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

        dict_vars['message'] += f" Ramp output {output_id} CH{channel} ({output.name}) " \
                                f"duty cycle from {start} % to {end} % in increments " \
                                f"of {increment} over {duration} seconds."

        change_in_duty_cycle = abs(start - end)
        steps = change_in_duty_cycle * 1 / increment
        seconds_per_step = duration / steps

        current_duty_cycle = start

        output_on = threading.Thread(
            target=self.control.output_on,
            args=(output_id,),
            kwargs={'output_type': 'pwm',
                    'amount': start,
                    'output_channel': channel})
        output_on.start()

        loop_running = True
        timer = time.time() + seconds_per_step
        while True:
            if timer < time.time():
                while timer < time.time():
                    timer += seconds_per_step
                    if start < end:
                        current_duty_cycle += increment
                        if current_duty_cycle > end:
                            current_duty_cycle = end
                            loop_running = False
                    else:
                        current_duty_cycle -= increment
                        if current_duty_cycle < end:
                            current_duty_cycle = end
                            loop_running = False

                output_on = threading.Thread(
                    target=self.control.output_on,
                    args=(output_id,),
                    kwargs={'output_type': 'pwm',
                            'amount': current_duty_cycle,
                            'output_channel': channel})
                output_on.start()

                if not loop_running:
                    break

        self.logger.debug(f"Message: {dict_vars['message']}")

        return dict_vars

    def is_setup(self):
        return self.action_setup
