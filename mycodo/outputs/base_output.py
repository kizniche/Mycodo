# coding=utf-8
"""
This module contains the AbstractOutput Class which acts as a template
for all outputs. It is not to be used directly. The AbstractOutput Class
ensures that certain methods and instance variables are included in each
Output.

All Outputs should inherit from this class and overwrite methods that raise
NotImplementedErrors
"""
import datetime
import logging
import threading
import time
import timeit

from sqlalchemy import and_
from sqlalchemy import or_

from mycodo.abstract_base_controller import AbstractBaseController
from mycodo.databases.models import Output
from mycodo.databases.models import OutputChannel
from mycodo.databases.models import Trigger
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import write_influxdb_value
from mycodo.utils.outputs import output_types


class AbstractOutput(AbstractBaseController):
    """
    Base Output class that ensures certain methods and values are present
    in outputs.
    """
    def __init__(self, output, testing=False, name=__name__):
        if not testing:
            super().__init__(output.unique_id, testing=testing, name=__name__)
        else:
            super().__init__(None, testing=testing, name=__name__)

        self.output_setup = False
        self.startup_timer = timeit.default_timer()
        self.control = DaemonControl()

        self.logger = None
        self.setup_logger(testing=testing, name=name, output_dev=output)

        self.OUTPUT_INFORMATION = None
        self.output_time_turned_on = {}
        self.output_on_duration = {}
        self.output_last_duration = {}
        self.output_on_until = {}
        self.output_off_until = {}
        self.output_off_triggered = {}
        self.output_states = {}

        self.output = output
        self.running = True

        if not testing:
            self.output_types = output_types()
            self.unique_id = output.unique_id
            self.output_name = self.output.name
            self.output_type = self.output.output_type

    def __iter__(self):
        """Support the iterator protocol."""
        return self

    def __repr__(self):
        """Representation of object."""
        return_str = f'<{type(self).__name__}'
        return_str += '>'
        return return_str

    def __str__(self):
        """Return measurement information."""
        return_str = ''
        return return_str

    def output_switch(self, state, output_type=None, amount=None, duty_cycle=None, output_channel=None):
        self.logger.error(
            f"{type(self).__name__} did not overwrite the output_switch() method. All "
            "subclasses of the AbstractOutput class are required to overwrite "
            "this method")
        raise NotImplementedError

    def is_on(self, output_channel=None):
        self.logger.error(
            f"{type(self).__name__} did not overwrite the is_on() method. All "
            "subclasses of the AbstractOutput class are required to overwrite "
            "this method")
        raise NotImplementedError

    def is_setup(self):
        self.logger.error(
            f"{type(self).__name__} did not overwrite the is_setup() method. All "
            "subclasses of the AbstractOutput class are required to overwrite "
            "this method")
        raise NotImplementedError

    def initialize(self):
        self.logger.error(
            f"{type(self).__name__} did not overwrite the initialize() method. All "
            "subclasses of the AbstractOutput class are required to overwrite "
            "this method")
        raise NotImplementedError

    def stop_output(self):
        """Called when Output is stopped."""
        self.running = False

    #
    # Do not overwrite the function below
    #

    def init_post(self):
        self.logger.info(f"Initialized in {(timeit.default_timer() - self.startup_timer) * 1000:.1f} ms")

    def setup_logger(self, testing=None, name=None, output_dev=None):
        name = name if name else __name__
        if not testing and output_dev:
            log_name = f"{name}_{output_dev.unique_id.split('-')[0]}"
        else:
            log_name = name
        self.logger = logging.getLogger(log_name)
        if not testing and output_dev:
            if output_dev.log_level_debug:
                self.logger.setLevel(logging.DEBUG)
            else:
                self.logger.setLevel(logging.INFO)

    def setup_on_off_output(self, output_information):
        """Deprecated TODO: Remove."""
        self.setup_output_variables(output_information)

    def setup_output_variables(self, output_information):
        self.OUTPUT_INFORMATION = output_information
        self.output_states = {}
        self.output_off_triggered = {}
        self.output_time_turned_on = {}
        self.output_on_duration = {}
        self.output_last_duration = {}
        self.output_off_until = {}

        if "on_off" in output_information['output_types']:
            self.output_on_until = {}

        for each_output_channel in output_information['channels_dict']:
            self.output_states[each_output_channel] = None
            self.output_off_triggered[each_output_channel] = False
            self.output_time_turned_on[each_output_channel] = None
            self.output_on_duration[each_output_channel] = False
            self.output_last_duration[each_output_channel] = 0
            self.output_off_until[each_output_channel] = 0

            if "on_off" in output_information['output_types']:
                self.output_on_until[each_output_channel] = datetime.datetime.now()

    def shutdown(self, shutdown_timer):
        self.stop_output()
        self.logger.info(f"Stopped in {(timeit.default_timer() - shutdown_timer) * 1000:.1f} ms")

    def output_on_off(self,
                      state,
                      output_channel=0,
                      output_type=None,
                      amount=0.0,
                      min_off=0.0,
                      trigger_conditionals=True,
                      additional_options=None):
        """
        Manipulate an output by passing on/off, a volume, or a PWM duty cycle
        to the output module.

        :param state: What state is desired? 'on', 1, True or 'off', 0, False
        :type state: str or int or bool
        :param output_channel: Channel of output
        :type output_channel: int
        :param output_type: The type of output ('sec', 'vol', 'value', 'pwm')
        :type output_type: str
        :param amount: If state is 'on', an amount can be set (e.g. duration to stay on, volume to output, etc.)
        :type amount: float
        :param min_off: Don't allow on again for at least this amount (0 = disabled)
        :type min_off: float
        :param trigger_conditionals: Whether to allow trigger conditionals to act or not
        :type trigger_conditionals: bool
        :param additional_options: dict
        :type additional_options: Additional options passed to the output controller
        """
        msg = ''

        self.logger.debug(
            f"output_on_off({state}, {output_channel}, {output_type}, "
            f"{amount}, {min_off}, {trigger_conditionals})")

        if state not in ['on', 1, True, 'off', 0, False]:
            return 1, 'state not "on", 1, True, "off", 0, or False'
        elif state in ['on', 1, True]:
            state = 'on'
        elif state in ['off', 0, False]:
            state = 'off'

        current_time = datetime.datetime.now()

        if amount is None:
            amount = 0

        output_is_on = self.is_on(output_channel)

        # Check if output channel exists
        if output_channel not in self.output_states:
            msg = f"Cannot manipulate Output {self.unique_id}: output channel doesn't exist: {output_channel}"
            self.logger.error(msg)
            return 1, msg

        # Check if output is set up
        if not self.is_setup():
            msg = f"Cannot manipulate Output {self.unique_id}: Output not set up."
            self.logger.error(msg)
            return 1, msg

        #
        # Signaled to turn output on
        #
        if state == 'on':

            # Checks if device is not on and is instructed to turn on
            if (output_type in ['sec', None] and
                    self.output_type in self.output_types['on_off'] and
                    not output_is_on):

                # Check if time is greater than off_until to allow an output on.
                # If the output is supposed to be off for a minimum duration and that amount
                # of time has not passed, do not allow the output to be turned on.
                off_until_datetime = self.output_off_until[output_channel]
                if off_until_datetime and off_until_datetime > current_time:
                    off_seconds = (off_until_datetime - current_time).total_seconds()
                    msg = f"Output {self.unique_id} CH{output_channel} ({self.output_name}) " \
                          "instructed to turn on, however the output has been instructed to stay " \
                          f"off for {off_seconds:.2f} more seconds."
                    self.logger.debug(msg)
                    return 1, msg

            # Output type: volt, set amount
            if output_type == 'value' and self.output_type in self.output_types['value']:
                self.output_switch(
                    'on',
                    output_type='value',
                    amount=amount,
                    output_channel=output_channel)

                msg = f"Command sent: Output {self.unique_id} CH{output_channel} " \
                      f"({self.output_name}) value: {amount:.1f} "

            # Output type: Volume, set amount
            if output_type == 'vol' and self.output_type in self.output_types['volume']:
                self.output_switch(
                    'on',
                    output_type='vol',
                    amount=amount,
                    output_channel=output_channel)

                msg = f"Command sent: Output {self.unique_id} CH{output_channel} " \
                      f"({self.output_name}) volume: {amount:.1f} "

            # Output type: PWM, set duty cycle
            elif output_type == 'pwm' and self.output_type in self.output_types['pwm']:
                out_ret = self.output_switch(
                    'on',
                    output_type='pwm',
                    amount=amount,
                    output_channel=output_channel)

                msg = f"Command sent: Output {self.unique_id} CH{output_channel} ({self.output_name}) " \
                      f"duty cycle: {amount:.2f} %. Output returned: {out_ret}"

            # Output type: On/Off, set duration for on state
            elif (output_type in ['sec', None] and
                    self.output_type in self.output_types['on_off'] and
                    amount != 0):
                # If a minimum off duration is set, determine the time the output is allowed to turn on again
                if min_off:
                    self.output_off_until[output_channel] = (
                        current_time + datetime.timedelta(seconds=abs(amount) + min_off))

                # Output is already on for an amount, update duration on with new end time
                if output_is_on and self.output_on_duration[output_channel]:
                    if self.output_on_until[output_channel] > current_time:
                        remaining_time = (
                            self.output_on_until[output_channel] - current_time).total_seconds()
                    else:
                        remaining_time = 0

                    time_on = abs(self.output_last_duration[output_channel]) - remaining_time
                    msg = f"Output {self.unique_id} CH{output_channel} ({self.output_name}) is already on for an " \
                          f"amount of {abs(self.output_last_duration[output_channel]):.2f} seconds " \
                          f"(with {remaining_time:.2f} seconds remaining). Recording the amount of time " \
                          f"the output has been on ({time_on:.2f} sec) and updating the amount " \
                          f"to {abs(amount):.2f} seconds."
                    self.logger.debug(msg)
                    self.output_on_until[output_channel] = (
                        current_time + datetime.timedelta(seconds=abs(amount)))
                    self.output_last_duration[output_channel] = amount

                    # Write the amount the output was ON to the
                    # database at the timestamp it turned ON
                    if time_on > 0:
                        # Make sure the recorded value is recorded negative
                        # if instructed to do so
                        if self.output_last_duration[output_channel] < 0:
                            duration_on = float(-time_on)
                        else:
                            duration_on = float(time_on)
                        timestamp = datetime.datetime.utcnow() - datetime.timedelta(seconds=abs(duration_on))

                        write_db = threading.Thread(
                            target=write_influxdb_value,
                            args=(self.unique_id,
                                  's',
                                  duration_on,),
                            kwargs={'measure': 'duration_time',
                                    'channel': output_channel,
                                    'timestamp': timestamp})
                        write_db.start()

                    return 0, msg

                # Output is on, but not for an amount
                elif output_is_on and not self.output_on_duration[output_channel]:

                    self.output_on_duration[output_channel] = True
                    self.output_on_until[output_channel] = (
                        current_time + datetime.timedelta(seconds=abs(amount)))
                    self.output_last_duration[output_channel] = amount
                    msg = f"Output {self.unique_id} CH{output_channel} ({self.output_name}) is " \
                          f"currently on without an amount. Turning into an amount of {abs(amount):.1f} seconds."
                    self.logger.debug(msg)
                    return 0, msg

                # Output is not already on
                else:
                    out_ret = self.output_switch(
                        'on', output_type='sec', amount=amount, output_channel=output_channel)

                    msg = f"Output {self.unique_id} CH{output_channel} ({self.output_name}) " \
                          f"on for {abs(amount):.1f} seconds. Output returned: {out_ret}"
                    self.logger.debug(msg)

                    self.output_on_until[output_channel] = (
                        current_time + datetime.timedelta(seconds=abs(amount)))
                    self.output_last_duration[output_channel] = amount
                    self.output_on_duration[output_channel] = True

            # No duration specific, so just turn output on
            elif ('output_types' in self.OUTPUT_INFORMATION and
                    'on_off' in self.OUTPUT_INFORMATION['output_types'] and
                    amount in [None, 0] and
                    output_type in ['sec', None]):

                try:
                    force_output_channel = self.options_channels["command_force"][output_channel]
                except:
                    force_output_channel = False

                # Don't turn on if already on, except if it can be forced on
                if output_is_on and not force_output_channel:
                    msg = f"Output {self.unique_id} CH{output_channel} ({self.output_name}) is already on."
                    self.logger.debug(msg)
                    return 1, msg
                else:
                    # Record the time the output was turned on in order to
                    # calculate and log the total amount was on, when
                    # it eventually turns off.
                    if not self.output_time_turned_on[output_channel]:
                        self.output_time_turned_on[output_channel] = current_time

                    ret_value = self.output_switch(
                        'on', output_channel=output_channel, output_type='sec')

                    msg = f"Output {self.unique_id} CH{output_channel} ({self.output_name}) " \
                          f"ON at {self.output_time_turned_on[output_channel]}. Output returned: {ret_value}"
                    self.logger.debug(msg)

        #
        # Signaled to turn output off
        #
        elif state == 'off':

            ret_value = self.output_switch('off', output_type=output_type, output_channel=output_channel)

            timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            msg = f"Output {self.unique_id} CH{output_channel} ({self.output_name}) " \
                  f"OFF at {timestamp}. Output returned: {ret_value}"
            self.logger.debug(msg)

            # Write output amount to database
            if (self.output_time_turned_on[output_channel] is not None or
                    self.output_on_duration[output_channel]):
                duration_sec = None
                timestamp = None

                if self.output_on_duration[output_channel]:
                    remaining_time = 0
                    if self.output_on_until[output_channel] > current_time:
                        remaining_time = (
                            self.output_on_until[output_channel] - current_time).total_seconds()
                    duration_sec = (abs(self.output_last_duration[output_channel]) - remaining_time)
                    timestamp = (datetime.datetime.utcnow() - datetime.timedelta(seconds=duration_sec))

                    # Store negative amount if a negative amount is received
                    if self.output_last_duration[output_channel] < 0:
                        duration_sec = -duration_sec

                    self.output_on_duration[output_channel] = False
                    self.output_on_until[output_channel] = current_time

                if self.output_time_turned_on[output_channel] is not None:
                    # Write the amount the output was ON to the database
                    # at the timestamp it turned ON
                    duration_sec = (
                        current_time - self.output_time_turned_on[output_channel]).total_seconds()
                    timestamp = datetime.datetime.utcnow() - datetime.timedelta(seconds=duration_sec)
                    self.output_time_turned_on[output_channel] = None

                # determine which measurement of the output_channel is a duration
                measurement_channel = None
                if ('channels_dict' in self.OUTPUT_INFORMATION and
                        'measurements_dict' in self.OUTPUT_INFORMATION):
                    measurement_channels = self.OUTPUT_INFORMATION['channels_dict'][output_channel]['measurements']
                    for each_measure_channel in measurement_channels:
                        if self.OUTPUT_INFORMATION['measurements_dict'][each_measure_channel]['unit'] == 's':
                            measurement_channel = each_measure_channel
                            break

                write_db = threading.Thread(
                    target=write_influxdb_value,
                    args=(self.unique_id,
                          's',
                          duration_sec,),
                    kwargs={'measure': 'duration_time',
                            'channel': measurement_channel,
                            'timestamp': timestamp})
                write_db.start()

            self.output_off_triggered[output_channel] = False

        if trigger_conditionals:
            try:
                self.check_triggers(self.unique_id, amount=amount, output_channel=output_channel)
            except Exception as err:
                self.logger.error(
                    f"Could not check Trigger for channel {output_channel} of output {self.unique_id}: {err}")

        return 0, msg

    def check_triggers(self, output_id, amount=None, output_channel=0):
        """
        This function is executed whenever an output is turned on or off
        It is responsible for executing Output Triggers
        """
        output_channel_dev = db_retrieve_table_daemon(OutputChannel).filter(
            and_(OutputChannel.output_id == output_id, OutputChannel.channel == output_channel)).first()
        if output_channel_dev is None:
            self.logger.error("Could not find channel in database")
            return

        #
        # Check On/Off Outputs
        #
        trigger_output = db_retrieve_table_daemon(Trigger)
        trigger_output = trigger_output.filter(Trigger.trigger_type == 'trigger_output')
        trigger_output = trigger_output.filter(Trigger.unique_id_1 == output_id)
        trigger_output = trigger_output.filter(Trigger.unique_id_2 == output_channel_dev.unique_id)
        trigger_output = trigger_output.filter(Trigger.is_activated.is_(True))

        # Find any Output Triggers with the output_id of the output that
        # just changed its state
        if self.is_on(output_channel):
            trigger_output = trigger_output.filter(
                or_(Trigger.output_state == 'on_duration_none',
                    Trigger.output_state == 'on_duration_any',
                    Trigger.output_state == 'on_duration_none_any',
                    Trigger.output_state == 'on_duration_equal',
                    Trigger.output_state == 'on_duration_greater_than',
                    Trigger.output_state == 'on_duration_equal_greater_than',
                    Trigger.output_state == 'on_duration_less_than',
                    Trigger.output_state == 'on_duration_equal_less_than'))

            on_duration_none = and_(
                Trigger.output_state == 'on_duration_none',
                amount == 0.0)

            on_duration_any = and_(
                Trigger.output_state == 'on_duration_any',
                bool(amount))

            on_duration_none_any = Trigger.output_state == 'on_duration_none_any'

            on_duration_equal = and_(
                Trigger.output_state == 'on_duration_equal',
                Trigger.output_duration == amount)

            on_duration_greater_than = and_(
                Trigger.output_state == 'on_duration_greater_than',
                amount > Trigger.output_duration)

            on_duration_equal_greater_than = and_(
                Trigger.output_state == 'on_duration_equal_greater_than',
                amount >= Trigger.output_duration)

            on_duration_less_than = and_(
                Trigger.output_state == 'on_duration_less_than',
                amount < Trigger.output_duration)

            on_duration_equal_less_than = and_(
                Trigger.output_state == 'on_duration_equal_less_than',
                amount <= Trigger.output_duration)

            trigger_output = trigger_output.filter(
                or_(on_duration_none,
                    on_duration_any,
                    on_duration_none_any,
                    on_duration_equal,
                    on_duration_greater_than,
                    on_duration_equal_greater_than,
                    on_duration_less_than,
                    on_duration_equal_less_than))
        else:
            trigger_output = trigger_output.filter(
                Trigger.output_state == 'off')

        # Execute the Trigger Actions for each Output Trigger
        # for this particular Output device
        for each_trigger in trigger_output.all():
            timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            message = f"{timestamp}\n[Trigger {each_trigger.unique_id.split('-')[0]} ({each_trigger.name})] " \
                      f"Output {output_id} CH{output_channel} {each_trigger.output_state}"

            self.control.trigger_all_actions(
                each_trigger.unique_id, message=message)

        #
        # Check PWM Outputs
        #
        trigger_output_pwm = db_retrieve_table_daemon(Trigger)
        trigger_output_pwm = trigger_output_pwm.filter(Trigger.trigger_type == 'trigger_output_pwm')
        trigger_output_pwm = trigger_output_pwm.filter(Trigger.unique_id_1 == output_id)
        trigger_output_pwm = trigger_output_pwm.filter(Trigger.unique_id_2 == output_channel_dev.unique_id)
        trigger_output_pwm = trigger_output_pwm.filter(Trigger.is_activated.is_(True))

        # Execute the Trigger Actions for each Output Trigger
        # for this particular Output device
        for each_trigger in trigger_output_pwm.all():
            trigger_trigger = False
            duty_cycle = self.output_state(output_channel)

            if duty_cycle == 'off':
                if (
                        (each_trigger.output_state == 'equal' and
                         each_trigger.output_duty_cycle == 0) or
                        (each_trigger.output_state == 'below' and
                         each_trigger.output_duty_cycle != 0)
                        ):
                    trigger_trigger = True
            elif (
                    (each_trigger.output_state == 'above' and
                     duty_cycle > each_trigger.output_duty_cycle) or
                    (each_trigger.output_state == 'below' and
                     duty_cycle < each_trigger.output_duty_cycle) or
                    (each_trigger.output_state == 'equal' and
                     duty_cycle == each_trigger.output_duty_cycle)
                    ):
                trigger_trigger = True

            if not trigger_trigger:
                continue

            timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            message = f"{timestamp}\n[Trigger {each_trigger.unique_id.split('-')[0]} ({each_trigger.name})] " \
                      f"Output {output_id} CH{output_channel} Duty Cycle {duty_cycle} " \
                      f"{each_trigger.output_state} {each_trigger.output_duty_cycle}"

            # Check triggers whenever an output is manipulated
            self.control.trigger_all_actions(each_trigger.unique_id, message=message)

    def output_sec_currently_on(self, output_channel):
        """Return how many seconds an output has been currently on for."""
        if not self.is_on(output_channel):
            return 0
        else:
            now = datetime.datetime.now()
            sec_currently_on = 0
            if self.output_on_duration[output_channel]:
                left = 0
                if self.output_on_until[output_channel] > now:
                    left = (self.output_on_until[output_channel] - now).total_seconds()
                sec_currently_on = abs(self.output_last_duration[output_channel]) - left
            elif self.output_time_turned_on[output_channel]:
                sec_currently_on = (now - self.output_time_turned_on[output_channel]).total_seconds()
            return sec_currently_on

    def output_state(self, output_channel):
        """
        Return the state of an output

        :param output_channel: Channel of the output
        :type output_channel: int

        :return: "on", "off", or duty cycle (for PWM output)
        :rtype: str
        """
        state = self.is_on(output_channel)
        if state is not None:
            if self.output_type in self.output_types['pwm'] + self.output_types['value']:
                if state:
                    return state
                elif state == 0 or state is False:
                    return 'off'
            elif state:
                return 'on'
            else:
                return 'off'

    def set_custom_option(self, option, value):
        return self._set_custom_option(Output, self.unique_id, option, value)

    def get_custom_option(self, option, default_return=None):
        return self._get_custom_option(Output, self.unique_id, option, default_return=default_return)

    def delete_custom_option(self, option):
        return self._delete_custom_option(Output, self.unique_id, option)

    def set_custom_channel_option(self, channel, option, value):
        return self._set_custom_channel_option(Output, self.unique_id, channel, option, value)

    def get_custom_channel_option(self, channel, option):
        return self._get_custom_channel_option(Output, self.unique_id, channel, option)

    def delete_custom_channel_option(self, channel, option):
        return self._delete_custom_channel_option(Output, self.unique_id, channel, option)
