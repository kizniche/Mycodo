# coding=utf-8
import logging
import threading
import time

import RPi.GPIO as GPIO

from mycodo.devices.camera import camera_record
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import read_last_influxdb
from mycodo.utils.send_data import send_email
from mycodo.utils.system_pi import cmd_output

logger = logging.getLogger("mycodo.utils.conditional")


def check_conditionals(self, cond_id, control,
                       Camera, Conditional, ConditionalActions, Input, Math, Output, PID, SMTP):
    """
    Check if any input conditional statements are activated and
    execute their actions if the conditional is true.

    For example, if measured temperature is above 30C, notify me@gmail.com

    :param self:
    :param cond_id:
    :param control:
    :param Camera:
    :param Conditional:
    :param ConditionalActions:
    :param Input:
    :param Math:
    :param Output:
    :param PID:
    :param SMTP:
    :return:
    """
    logger_cond = logging.getLogger("mycodo.utils.conditional_{id}".format(
        id=cond_id))

    cond = db_retrieve_table_daemon(
        Conditional, device_id=cond_id, entry='first')

    message = "[Conditional: {name} ({id})]".format(
        name=cond.name,
        id=cond_id)

    device_id = cond.if_sensor_measurement.split(',')[0]
    device_measurement = cond.if_sensor_measurement.split(',')[1]
    direction = cond.if_sensor_direction
    setpoint = cond.if_sensor_setpoint
    period = cond.if_sensor_period

    device = None

    input_dev = db_retrieve_table_daemon(
        Input, unique_id=device_id, entry='first')
    if input_dev:
        device = input_dev

    math = db_retrieve_table_daemon(
        Math, unique_id=device_id, entry='first')
    if math:
        device = math

    output = db_retrieve_table_daemon(
        Output, unique_id=device_id, entry='first')
    if output:
        device = output

    pid = db_retrieve_table_daemon(
        PID, unique_id=device_id, entry='first')
    if pid:
        device = pid

    if not device:
        message += " Error: Controller not Input, Math, Output, or PID"
        logger_cond.error(message)
        return

    last_measurement = None

    if direction and device_id and device_measurement:

        # Check if there hasn't been a measurement in the last set number
        # of seconds. If not, trigger conditional
        if direction == 'none_found':
            duration_seconds = setpoint
            last_measurement = get_last_measurement(
                device_id, device_measurement, duration_seconds)
            if not last_measurement:
                message += " {meas} measurement for device ID {id} not found in the past" \
                           " {value} seconds.".format(
                            meas=device_measurement,
                            id=device_id,
                            value=duration_seconds)
            else:
                return

        # Check if last measurement is greater or less than the set value
        else:
            last_measurement = get_last_measurement(
                device_id,
                device_measurement,
                int(period * 1.5))
            if not last_measurement:
                logger_cond.debug("Last measurement not found")
                return
            elif ((direction == 'above' and
                   last_measurement > setpoint) or
                  (direction == 'below' and
                   last_measurement < setpoint)):

                message += " {meas}: {value} ".format(
                    meas=device_measurement,
                    value=last_measurement)
                if direction == 'above':
                    message += "(>"
                elif direction == 'below':
                    message += "(<"
                message += " {sp} set value).".format(
                    sp=setpoint)
            else:
                return  # Not triggered

    # If the edge detection variable is set, calling this function will
    # trigger an edge detection event. This will merely produce the correct
    # message based on the edge detection settings.
    elif cond.if_sensor_edge_detected:
        if cond.if_sensor_edge_select == 'edge':
            message += " {edge} Edge Detected.".format(
                edge=cond.if_sensor_edge_detected)
        elif cond.if_sensor_edge_select == 'state':
            if (output and
                    output.pin and
                    GPIO.input(int(output.pin)) == cond.if_sensor_gpio_state):
                message += " {state} GPIO State Detected.".format(
                    state=cond.if_sensor_gpio_state)
        else:
            # Not configured correctly or GPIO state not verified
            return

    # If the code hasn't returned by now, the conditional has been triggered
    # and the actions for that conditional should be executed
    trigger_conditional_actions(self, cond_id, device_id, device_measurement, control,
                                Camera, ConditionalActions, Input, Math, PID, SMTP,
                                message=message, last_measurement=last_measurement)


def trigger_conditional_actions(
        self, cond_id, device_id, device_measurement, control,
        Camera, ConditionalActions, Input, Math, PID, SMTP,
        message='', last_measurement=None):
    """
    If a Conditional has been triggered, this function will execute
    the Conditional Actions

    :param self: self from the Controller class
    :param cond_id: The ID of the Conditional
    :param device_id: The unique ID associated with the device_measurement
    :param device_measurement: The measurement (i.e. "temperature")
    :param control: The Daemon control function
    :param Camera: Camera database model
    :param Conditional: Conditional database model
    :param ConditionalActions: ConditionalActions database model
    :param Input: Input database model
    :param Math: Math database model
    :param PID: PID database model
    :param SMTP: SMTP database model
    :param message: The message generated from the conditional check
    :param last_measurement: The last measurement value
    :return: 
    """
    logger_cond = logging.getLogger("mycodo.utils.conditional_actions_{id}".format(
        id=cond_id))

    cond_actions = db_retrieve_table_daemon(ConditionalActions)
    cond_actions = cond_actions.filter(
        ConditionalActions.conditional_id == cond_id).all()

    attachment_file = False
    attachment_type = False
    device = None

    input_dev = db_retrieve_table_daemon(
        Input, unique_id=device_id, entry='first')
    if input_dev:
        device = input_dev

    math = db_retrieve_table_daemon(
        Math, unique_id=device_id, entry='first')
    if math:
        device = math

    pid = db_retrieve_table_daemon(
        PID, unique_id=device_id, entry='first')
    if pid:
        device = pid

    for cond_action in cond_actions:
        message += " Conditional Action ({id}): {do_action}.".format(
            id=cond_action.id, do_action=cond_action.do_action)

        # Actuate output
        if (cond_action.do_action == 'output' and cond_action.do_relay_id and
                cond_action.do_relay_state in ['on', 'off']):
            message += " Turn output {id} {state}".format(
                id=cond_action.do_relay_id,
                state=cond_action.do_relay_state)
            if (cond_action.do_relay_state == 'on' and
                    cond_action.do_relay_duration):
                message += " for {sec} seconds".format(
                    sec=cond_action.do_relay_duration)
            message += "."

            output_on_off = threading.Thread(
                target=control.output_on_off,
                args=(cond_action.do_relay_id,
                      cond_action.do_relay_state,),
                kwargs={'duration': cond_action.do_relay_duration})
            output_on_off.start()

        # Execute command in shell
        elif cond_action.do_action == 'command':

            # Replace string variables with actual values
            command_str = cond_action.do_action_string
            if last_measurement:
                command_str = command_str.replace(
                    "((measure_{var}))".format(
                        var=device_measurement), str(last_measurement))

            # If measurement is from an Input, and the measurement is
            # linux_command or location, replace with that variable
            if input_dev and device_measurement == input_dev.cmd_measurement:
                command_str = command_str.replace(
                    "((measure_linux_command))", str(input_dev.location))
            if input_dev:
                command_str = command_str.replace(
                    "((measure_location))", str(input_dev.location))

            # Replacement string is the device period
            # Must be Input, Math, or PID
            if device and device.period:
                command_str = command_str.replace(
                    "((measure_period))", str(device.period))

            message += " Execute '{com}' ".format(
                com=command_str)

            _, _, cmd_status = cmd_output(command_str)

            message += "(Status: {stat}).".format(stat=cmd_status)

        # Capture photo
        elif cond_action.do_action in ['photo', 'photo_email']:
            message += "  Capturing photo with camera ({id}).".format(
                id=cond_action.do_camera_id)
            camera_still = db_retrieve_table_daemon(
                Camera, device_id=cond_action.do_camera_id)
            attachment_file = camera_record('photo', camera_still)

        # Capture video
        elif cond_action.do_action in ['video', 'video_email']:
            message += "  Capturing video with camera ({id}).".format(
                id=cond_action.do_camera_id)
            camera_stream = db_retrieve_table_daemon(
                Camera, device_id=cond_action.do_camera_id)
            attachment_file = camera_record(
                'video', camera_stream,
                duration_sec=cond_action.do_camera_duration)

        # Activate PID controller
        elif cond_action.do_action == 'activate_pid':
            message += " Activate PID ({id}).".format(
                id=cond_action.do_pid_id)
            pid = db_retrieve_table_daemon(
                PID, device_id=cond_action.do_pid_id, entry='first')
            if pid.is_activated:
                message += " Notice: PID is already active!"
            else:
                activate_pid = threading.Thread(
                    target=control.controller_activate,
                    args=('PID',
                          cond_action.do_pid_id,))
                activate_pid.start()

        # Deactivate PID controller
        elif cond_action.do_action == 'deactivate_pid':
            message += " Deactivate PID ({id}).".format(
                id=cond_action.do_pid_id)
            pid = db_retrieve_table_daemon(
                PID, device_id=cond_action.do_pid_id, entry='first')
            if not pid.is_activated:
                message += " Notice: PID is already inactive!"
            else:
                deactivate_pid = threading.Thread(
                    target=control.controller_deactivate,
                    args=('PID',
                          cond_action.do_pid_id,))
                deactivate_pid.start()

        elif cond_action.do_action in ['email',
                                       'photo_email',
                                       'video_email']:
            if (self.email_count >= self.smtp_max_count and
                    time.time() < self.smtp_wait_timer[cond_id]):
                self.allowed_to_send_notice = False
            else:
                if time.time() > self.smtp_wait_timer[cond_id]:
                    self.email_count = 0
                    self.smtp_wait_timer[cond_id] = time.time() + 3600
                self.allowed_to_send_notice = True
            self.email_count += 1

            # If the emails per hour limit has not been exceeded
            if self.allowed_to_send_notice:
                message += " Notify {email}.".format(
                    email=cond_action.do_action_string)
                # attachment_type != False indicates to
                # attach a photo or video
                if cond_action.do_action == 'photo_email':
                    message += " Photo attached to email."
                    attachment_type = 'still'
                elif cond_action.do_action == 'video_email':
                    message += " Video attached to email."
                    attachment_type = 'video'

                smtp = db_retrieve_table_daemon(SMTP, entry='first')
                send_email(smtp.host, smtp.ssl, smtp.port,
                           smtp.user, smtp.passw, smtp.email_from,
                           cond_action.do_action_string, message,
                           attachment_file, attachment_type)
            else:
                logger_cond.debug(
                    "Wait {sec:.0f} seconds to email again.".format(
                        sec=self.smtp_wait_timer[cond_id] - time.time()))

        elif cond_action.do_action == 'flash_lcd':
            message += " Flashing LCD ({id}).".format(
                id=cond_action.do_lcd_id)

            start_flashing = threading.Thread(
                target=control.flash_lcd,
                args=(cond_action.do_lcd_id, 1,))
            start_flashing.start()

    logger_cond.debug(message)


def get_last_measurement(unique_id, measurement, duration_sec):
    """
    Retrieve the latest input measurement

    :return: The latest input value or None if no data available
    :rtype: float or None

    :param unique_id: ID of controller
    :type unique_id: str
    :param measurement: Environmental condition of a input (e.g.
        temperature, humidity, pressure, etc.)
    :type measurement: str
    :param duration_sec: number of seconds to check for a measurement
        in the past.
    :type duration_sec: int
    """
    last_measurement = read_last_influxdb(
        unique_id, measurement,  duration_sec=duration_sec)

    if last_measurement:
        last_value = last_measurement[1]
        return last_value
