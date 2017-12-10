# coding=utf-8
import logging
import threading
import time
import RPi.GPIO as GPIO

from devices.camera import camera_record
from database import db_retrieve_table_daemon
from influx import read_last_influxdb
from send_data import send_email
from system_pi import cmd_output

logger = logging.getLogger("mycodo.utils.conditional")


def check_conditionals(self, cond_id, measurements, control,
                       Camera, Conditional, ConditionalActions, Input, Math, PID, SMTP):
    """
    Check if any input conditional statements are activated and
    execute their actions if the conditional is true.

    For example, if measured temperature is above 30C, notify me@gmail.com

    :param self:
    :param cond_id:
    :param measurements:
    :param control:
    :param Camera:
    :param Conditional:
    :param ConditionalActions:
    :param Input:
    :param Math:
    :param PID:
    :param SMTP:
    :return:
    """
    logger_cond = logging.getLogger("mycodo.utils.conditional_{id}".format(
        id=cond_id))
    attachment_file = False
    attachment_type = False

    cond = db_retrieve_table_daemon(
        Conditional, device_id=cond_id, entry='first')

    message = u"[Conditional: {name} ({id})]".format(
        name=cond.name,
        id=cond_id)

    input_dev = db_retrieve_table_daemon(
        Input, device_id=cond_id, entry='first')
    math = db_retrieve_table_daemon(
        Math, device_id=cond_id, entry='first')

    if not input_dev and not math:
        message += u" Error: Controller not Input or Math"
        logger_cond.error(message)
        return

    if cond.if_sensor_direction:
        if cond.if_sensor_direction == 'none_found':
            duration_seconds = cond.if_sensor_setpoint
            last_measurement = get_last_measurement(
                self.unique_id, cond.if_sensor_measurement, duration_seconds)
            if last_measurement:
                return  # Don't trigger "measurement not found"
            message += u" {meas} measurement not found in the past" \
                       u" {value} seconds.".format(
                        meas=cond.if_sensor_measurement,
                        value=duration_seconds)

        else:
            last_measurement = get_last_measurement(
                self.unique_id,
                cond.if_sensor_measurement,
                int(self.period * 1.5))
            if not last_measurement:
                logger_cond.debug("Last measurement not found")
                return
            elif ((cond.if_sensor_direction == 'above' and
                   last_measurement > cond.if_sensor_setpoint) or
                  (cond.if_sensor_direction == 'below' and
                   last_measurement < cond.if_sensor_setpoint)):

                message += u" {meas}: {value} ".format(
                    meas=cond.if_sensor_measurement,
                    value=last_measurement)
                if cond.if_sensor_direction == 'above':
                    message += "(>"
                elif cond.if_sensor_direction == 'below':
                    message += "(<"
                message += u" {sp} set value).".format(
                    sp=cond.if_sensor_setpoint)
            else:
                return  # Not triggered
    elif cond.if_sensor_edge_detected:
        if cond.if_sensor_edge_select == 'edge':
            message += u" {edge} Edge Detected.".format(
                edge=cond.if_sensor_edge_detected)
        elif cond.if_sensor_edge_select == 'state':
            if (input_dev and
                    input_dev.location and
                    GPIO.input(int(input_dev.location)) == cond.if_sensor_gpio_state):
                message += u" {state} GPIO State Detected.".format(
                    state=cond.if_sensor_gpio_state)

    cond_actions = db_retrieve_table_daemon(ConditionalActions)
    cond_actions = cond_actions.filter(
        ConditionalActions.conditional_id == cond_id).all()

    for cond_action in cond_actions:
        message += u" Conditional Action ({id}): {do_action}.".format(
            id=cond_action.id, do_action=cond_action.do_action)

        # Actuate output
        if (cond_action.do_relay_id and
                cond_action.do_relay_state in ['on', 'off']):
            message += u" Turn output {id} {state}".format(
                id=cond_action.do_relay_id,
                state=cond_action.do_relay_state)
            if (cond_action.do_relay_state == 'on' and
                    cond_action.do_relay_duration):
                message += u" for {sec} seconds".format(
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
            for each_measurement, each_value in measurements.values.items():
                command_str = command_str.replace(
                    "(({var}))".format(var=each_measurement), str(each_value))
                if input_dev and each_measurement == input_dev.cmd_measurement:
                    command_str = command_str.replace(
                        "((linux_command))", str(input_dev.location))
            if input_dev:
                command_str = command_str.replace(
                    "((location))", str(input_dev.location))
            command_str = command_str.replace(
                "((period))", str(cond.cond_if_input_period[cond_id]))

            message += u" Execute '{com}' ".format(
                com=command_str)

            _, _, cmd_status = cmd_output(command_str)

            message += u"(Status: {stat}).".format(stat=cmd_status)

        # Capture photo
        elif cond_action.do_action in ['photo', 'photo_email']:
            message += u"  Capturing photo with camera ({id}).".format(
                id=cond_action.do_camera_id)
            camera_still = db_retrieve_table_daemon(
                Camera, device_id=cond_action.do_camera_id)
            attachment_file = camera_record('photo', camera_still)

        # Capture video
        elif cond_action.do_action in ['video', 'video_email']:
            message += u"  Capturing video with camera ({id}).".format(
                id=cond_action.do_camera_id)
            camera_stream = db_retrieve_table_daemon(
                Camera, device_id=cond_action.do_camera_id)
            attachment_file = camera_record(
                'video', camera_stream,
                duration_sec=cond_action.do_camera_duration)

        # Activate PID controller
        elif cond_action.do_action == 'activate_pid':
            message += u" Activate PID ({id}).".format(
                id=cond_action.do_pid_id)
            pid = db_retrieve_table_daemon(
                PID, device_id=cond_action.do_pid_id, entry='first')
            if pid.is_activated:
                message += u" Notice: PID is already active!"
            else:
                activate_pid = threading.Thread(
                    target=control.controller_activate,
                    args=('PID',
                          cond_action.do_pid_id,))
                activate_pid.start()

        # Deactivate PID controller
        elif cond_action.do_action == 'deactivate_pid':
            message += u" Deactivate PID ({id}).".format(
                id=cond_action.do_pid_id)
            pid = db_retrieve_table_daemon(
                PID, device_id=cond_action.do_pid_id, entry='first')
            if not pid.is_activated:
                message += u" Notice: PID is already inactive!"
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
                allowed_to_send_notice = False
            else:
                if time.time() > self.smtp_wait_timer[cond_id]:
                    self.email_count = 0
                    self.smtp_wait_timer[cond_id] = time.time() + 3600
                allowed_to_send_notice = True
            self.email_count += 1

            # If the emails per hour limit has not been exceeded
            if allowed_to_send_notice:
                message += u" Notify {email}.".format(
                    email=cond_action.do_action_string)
                # attachment_type != False indicates to
                # attach a photo or video
                if cond_action.do_action == 'photo_email':
                    message += u" Photo attached to email."
                    attachment_type = 'still'
                elif cond_action.do_action == 'video_email':
                    message += u" Video attached to email."
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
            message += u" Flashing LCD ({id}).".format(
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
