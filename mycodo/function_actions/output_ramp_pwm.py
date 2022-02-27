# coding=utf-8
import threading
import time

from flask_babel import lazy_gettext

from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import Actions
from mycodo.databases.models import Output
from mycodo.databases.models import OutputChannel
from mycodo.function_actions.base_function_action import AbstractFunctionAction
from mycodo.utils.constraints_pass import constraints_pass_positive_or_zero_value
from mycodo.utils.constraints_pass import constraints_pass_positive_value
from mycodo.utils.database import db_retrieve_table_daemon

FUNCTION_ACTION_INFORMATION = {
    'name_unique': 'output_ramp_pwm',
    'name': '{} ({} {})'.format(
            TRANSLATIONS['output']['title'],
            TRANSLATIONS['ramp']['title'],
            TRANSLATIONS['duty_cycle']['title']),
    'library': None,
    'manufacturer': 'Mycodo',

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': lazy_gettext('Ramp a PWM Output from one duty cycle to another duty cycle over a period of time.'),

    'usage': 'Executing <strong>self.run_action("{ACTION_ID}")</strong> will ramp the PWM output duty cycle according to the settings. '
             'Executing <strong>self.run_action("{ACTION_ID}", value=[42, 62, 1.0, 600])</strong> will ramp the PWM output duty cycle to the values sent (e.g. 42% to 62% at increments of 1.0 % 0ver 600 seconds).',

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
            'id': 'duty_cycle_start',
            'type': 'float',
            'default_value': 0.0,
            'required': True,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': "{}: {}".format(lazy_gettext('Duty Cycle'), lazy_gettext('Start')),
            'phrase': lazy_gettext('Duty cycle for the PWM (percent, 0.0 - 100.0)')
        },
        {
            'id': 'duty_cycle_end',
            'type': 'float',
            'default_value': 50.0,
            'required': True,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': "{}: {}".format(lazy_gettext('Duty Cycle'), lazy_gettext('End')),
            'phrase': lazy_gettext('Duty cycle for the PWM (percent, 0.0 - 100.0)')
        },
        {
            'id': 'duty_cycle_increment',
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
            'name': lazy_gettext('Duration (seconds)'),
            'phrase': 'How long to ramp from start to finish.'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """
    Function Action: Output (On/Off/Duration)
    """
    def __init__(self, action_dev, testing=False):
        super(ActionModule, self).__init__(action_dev, testing=testing, name=__name__)

        self.output_device_id = None
        self.output_measurement_id = None
        self.output_channel_id = None
        self.duty_cycle_start = None
        self.duty_cycle_end = None
        self.duty_cycle_increment = None
        self.duration = None

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
                duty_cycle_start = dict_vars["value"][0]
                duty_cycle_end = dict_vars["value"][1]
                increment = dict_vars["value"][2]
                duration = dict_vars["value"][3]
                values_set = True
            except:
                self.logger.exception("Error setting values passed to action")

        if not values_set:
            duty_cycle_start = self.duty_cycle_start
            duty_cycle_end = self.duty_cycle_end
            increment = self.duty_cycle_increment
            duration = self.duration

        output_channel = self.get_output_channel_from_channel_id(
            self.output_channel_id)

        this_output = db_retrieve_table_daemon(
            Output, unique_id=self.output_device_id, entry='first')
        message += " Ramp output {unique_id} CH{ch} ({id}, {name}) " \
                   "duty cycle from {fdc}% to {tdc}% in increments " \
                   "of {inc} over {sec} seconds.".format(
            unique_id=self.output_device_id,
            ch=self.output_channel_id,
            id=this_output.id,
            name=this_output.name,
            fdc=duty_cycle_start,
            tdc=duty_cycle_end,
            inc=increment,
            sec=duration)

        change_in_duty_cycle = abs(duty_cycle_start - duty_cycle_end)
        steps = change_in_duty_cycle * 1 / increment
        seconds_per_step = duration / steps

        current_duty_cycle = duty_cycle_start

        output_on = threading.Thread(
            target=self.control.output_on,
            args=(self.output_device_id,),
            kwargs={'output_type': 'pwm',
                    'amount': duty_cycle_start,
                    'output_channel': output_channel.channel})
        output_on.start()

        loop_running = True
        timer = time.time() + seconds_per_step
        while True:
            if timer < time.time():
                while timer < time.time():
                    timer += seconds_per_step
                    if duty_cycle_start < duty_cycle_end:
                        current_duty_cycle += increment
                        if current_duty_cycle > duty_cycle_end:
                            current_duty_cycle = duty_cycle_end
                            loop_running = False
                    else:
                        current_duty_cycle -= increment
                        if current_duty_cycle < duty_cycle_end:
                            current_duty_cycle = duty_cycle_end
                            loop_running = False

                output_on = threading.Thread(
                    target=self.control.output_on,
                    args=(self.output_device_id,),
                    kwargs={'output_type': 'pwm',
                            'amount': current_duty_cycle,
                            'output_channel': output_channel.channel})
                output_on.start()

                if not loop_running:
                    break

        return message

    def is_setup(self):
        return self.action_setup
