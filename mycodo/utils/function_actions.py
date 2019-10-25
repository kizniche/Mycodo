# coding=utf-8
import logging
import threading
import time

import RPi.GPIO as GPIO
import os

from mycodo.config import FUNCTION_ACTION_INFO
from mycodo.config import SQL_DATABASE_MYCODO
from mycodo.databases.models import Actions
from mycodo.databases.models import Camera
from mycodo.databases.models import Conditional
from mycodo.databases.models import ConditionalConditions
from mycodo.databases.models import Conversion
from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import Input
from mycodo.databases.models import LCD
from mycodo.databases.models import Math
from mycodo.databases.models import NoteTags
from mycodo.databases.models import Notes
from mycodo.databases.models import Output
from mycodo.databases.models import PID
from mycodo.databases.models import SMTP
from mycodo.databases.models import Trigger
from mycodo.databases.utils import session_scope
from mycodo.devices.camera import camera_record
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import read_last_influxdb
from mycodo.utils.influx import read_past_influxdb
from mycodo.utils.send_data import send_email
from mycodo.utils.system_pi import cmd_output
from mycodo.utils.system_pi import return_measurement_info

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO

logger = logging.getLogger("mycodo.function_actions")


def check_allowed_to_email():
    smtp_table = db_retrieve_table_daemon(SMTP, entry='first')
    smtp_max_count = smtp_table.hourly_max
    smtp_wait_timer = smtp_table.smtp_wait_timer
    email_count = smtp_table.email_count

    if (email_count >= smtp_max_count and
            time.time() < smtp_wait_timer):
        allowed_to_send_notice = False
    else:
        if time.time() > smtp_wait_timer:
            with session_scope(MYCODO_DB_PATH) as new_session:
                mod_smtp = new_session.query(SMTP).first()
                mod_smtp.email_count = 0
                mod_smtp.smtp_wait_timer = time.time() + 3600
                new_session.commit()
        allowed_to_send_notice = True

    with session_scope(MYCODO_DB_PATH) as new_session:
        mod_smtp = new_session.query(SMTP).first()
        mod_smtp.email_count += 1
        new_session.commit()

    return smtp_wait_timer, allowed_to_send_notice


def get_condition_value(condition_id):
    """
    Returns condition measurements for Conditional controllers
    :param condition_id: Conditional condition ID
    :return: measurement: multiple types
    """
    sql_condition = db_retrieve_table_daemon(ConditionalConditions).filter(
        ConditionalConditions.unique_id == condition_id).first()

    # Check Measurement Conditions
    if sql_condition.condition_type in ['measurement',
                                        'measurement_past_average',
                                        'measurement_past_sum']:
        device_id = sql_condition.measurement.split(',')[0]
        measurement_id = sql_condition.measurement.split(',')[1]

        device_measurement = db_retrieve_table_daemon(
            DeviceMeasurements, unique_id=measurement_id)
        if device_measurement:
            conversion = db_retrieve_table_daemon(
                Conversion, unique_id=device_measurement.conversion_id)
        else:
            conversion = None
        channel, unit, measurement = return_measurement_info(
            device_measurement, conversion)

        if None in [channel, unit]:
            logger.error(
                "Could not determine channel or unit from measurement ID: "
                "{}".format(measurement_id))
            return

        max_age = sql_condition.max_age

        if sql_condition.condition_type == 'measurement':
            return_measurement = get_last_measurement(
                device_id, unit, measurement, channel, max_age)
        elif sql_condition.condition_type == 'measurement_past_average':
            measurement_list = []
            measurements_str = get_past_measurements(
                device_id, unit, measurement, channel, max_age)
            for each_set in measurements_str.split(';'):
                measurement_list.append(float(each_set.split(',')[1]))
            return_measurement = sum(measurement_list) / len(measurement_list)
        elif sql_condition.condition_type == 'measurement_past_sum':
            measurement_list = []
            measurements_str = get_past_measurements(
                device_id, unit, measurement, channel, max_age)
            for each_set in measurements_str.split(';'):
                measurement_list.append(float(each_set.split(',')[1]))
            return_measurement = sum(measurement_list)
        else:
            return

        return return_measurement

    # Return GPIO state
    elif sql_condition.condition_type == 'gpio_state':
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(int(sql_condition.gpio_pin), GPIO.IN)
            gpio_state = GPIO.input(int(sql_condition.gpio_pin))
        except Exception as e:
            gpio_state = None
            logger.error("Exception reading the GPIO pin: {}".format(e))
        return gpio_state

    # Return output state
    elif sql_condition.condition_type == 'output_state':
        control = DaemonControl()
        return control.output_state(sql_condition.output_id)

    # Return the duration the output is currently on for
    elif sql_condition.condition_type == 'output_duration_on':
        control = DaemonControl()
        return control.output_sec_currently_on(sql_condition.output_id)

    # Return controller active state
    elif sql_condition.condition_type == 'controller_status':
        controller_type, _, _ = which_controller(sql_condition.controller_id)
        control = DaemonControl()
        return control.controller_is_active(
            controller_type, sql_condition.controller_id)


def get_condition_value_dict(condition_id):
    """
    Returns dict of multiple condition measurements for Conditional controllers
    :param condition_id: Conditional condition ID
    :return: measurement: dict of float measurements
    """
    # Check Measurement Conditions
    sql_condition = db_retrieve_table_daemon(ConditionalConditions).filter(
        ConditionalConditions.unique_id == condition_id).first()

    if sql_condition.condition_type == 'measurement_dict':
        device_id = sql_condition.measurement.split(',')[0]
        measurement_id = sql_condition.measurement.split(',')[1]

        device_measurement = db_retrieve_table_daemon(
            DeviceMeasurements, unique_id=measurement_id)
        if device_measurement:
            conversion = db_retrieve_table_daemon(
                Conversion, unique_id=device_measurement.conversion_id)
        else:
            conversion = None
        channel, unit, measurement = return_measurement_info(
            device_measurement, conversion)

        if None in [channel, unit]:
            logger.error(
                "Could not determine channel or unit from measurement ID: "
                "{}".format(measurement_id))
            return

        max_age = sql_condition.max_age
        # Check if there hasn't been a measurement in the last set number
        # of seconds. If not, trigger conditional
        past_measurements = get_past_measurements(
            device_id, unit, measurement, channel, max_age)
        return past_measurements


def get_last_measurement(unique_id, unit, measurement, channel, duration_sec):
    """
    Retrieve the latest input measurement

    :return: The latest input value or None if no data available
    :rtype: float or None

    :param unique_id: What unique_id tag to query in the Influxdb
        database (eg. '00000001')
    :type unique_id: str
    :param unit: What unit to query in the Influxdb
        database (eg. 'C', 's')
    :type unit: str
    :param measurement: What measurement to query in the Influxdb
        database (eg. 'temperature', 'duration_time')
    :type measurement: str or None
    :param channel: Channel
    :type channel: int or None
    :param duration_sec: How many seconds to look for a past measurement
    :type duration_sec: int or None
    """

    last_measurement = read_last_influxdb(
        unique_id,
        unit,
        measurement,
        channel,
        duration_sec=duration_sec)

    if last_measurement is not None:
        last_value = last_measurement[1]
        return last_value


def get_past_measurements(unique_id, unit, measurement, channel, duration_sec):
    """
    Retrieve the past input measurements

    :return: The latest input value or None if no data available
    :rtype: dict or None

    :param unique_id: What unique_id tag to query in the Influxdb
        database (eg. '00000001')
    :type unique_id: str
    :param unit: What unit to query in the Influxdb
        database (eg. 'C', 's')
    :type unit: str
    :param measurement: What measurement to query in the Influxdb
        database (eg. 'temperature', 'duration_time')
    :type measurement: str or None
    :param channel: Channel
    :type channel: int or None
    :param duration_sec: How many seconds to look for a past measurement
    :type duration_sec: int or None
    """

    past_measurements = read_past_influxdb(
        unique_id,
        unit,
        measurement,
        channel,
        past_seconds=duration_sec)

    if past_measurements:
        string_ts_values = ''
        for index, each_set in enumerate(past_measurements):
            string_ts_values += '{},{}'.format(each_set[0], each_set[1])
            if index + 1 < len(past_measurements):
                string_ts_values += ';'
        return string_ts_values


def action_pause(cond_action, message):
    message += " [{id}] Pause actions for {sec} seconds.".format(
        id=cond_action.id,
        sec=cond_action.pause_duration)

    time.sleep(cond_action.pause_duration)
    return message


def action_ir_send(cond_action, message):
    command = 'irsend SEND_ONCE {remote} {code}'.format(
        remote=cond_action.remote, code=cond_action.code)
    output, err, stat = cmd_output(command)

    # Send more than once
    if cond_action.send_times > 1:
        for _ in range(cond_action.send_times - 1):
            time.sleep(0.5)
            output, err, stat = cmd_output(command)

    message += " [{id}] Infrared Send " \
               "code '{code}', remote '{remote}', times: {times}:" \
               "\nOutput: {out}" \
               "\nError: {err}" \
               "\nStatus: {stat}'.".format(
        id=cond_action.id,
        code=cond_action.code,
        remote=cond_action.remote,
        times=cond_action.send_times,
        out=output,
        err=err,
        stat=stat)
    return message


def action_output(cond_action, message):
    control = DaemonControl()
    this_output = db_retrieve_table_daemon(
        Output, unique_id=cond_action.do_unique_id, entry='first')
    message += " Turn output {unique_id} ({id}, {name}) {state}".format(
        unique_id=cond_action.do_unique_id,
        id=this_output.id,
        name=this_output.name,
        state=cond_action.do_output_state)
    if (cond_action.do_output_state == 'on' and
            cond_action.do_output_duration):
        message += " for {sec} seconds".format(
            sec=cond_action.do_output_duration)
    message += "."

    output_on_off = threading.Thread(
        target=control.output_on_off,
        args=(cond_action.do_unique_id,
              cond_action.do_output_state,),
        kwargs={'amount': cond_action.do_output_duration})
    output_on_off.start()
    return message


def action_output_pwm(cond_action, message):
    control = DaemonControl()
    this_output = db_retrieve_table_daemon(
        Output, unique_id=cond_action.do_unique_id, entry='first')
    message += " Turn output {unique_id} ({id}, {name}) duty cycle to {duty_cycle}%.".format(
        unique_id=cond_action.do_unique_id,
        id=this_output.id,
        name=this_output.name,
        duty_cycle=cond_action.do_output_pwm)

    output_on = threading.Thread(
        target=control.output_on,
        args=(cond_action.do_unique_id,),
        kwargs={'duty_cycle': cond_action.do_output_pwm})
    output_on.start()
    return message


def action_output_ramp_pwm(cond_action, message):
    control = DaemonControl()
    this_output = db_retrieve_table_daemon(
        Output, unique_id=cond_action.do_unique_id, entry='first')
    message += " Ramp output {unique_id} ({id}, {name}) " \
               "duty cycle from {fdc}% to {tdc}% in increments " \
               "of {inc} over {sec} seconds.".format(
                    unique_id=cond_action.do_unique_id,
                    id=this_output.id,
                    name=this_output.name,
                    fdc=cond_action.do_output_pwm,
                    tdc=cond_action.do_output_pwm2,
                    inc=cond_action.do_action_string,
                    sec=cond_action.do_output_duration)

    if cond_action.do_action_string not in ['0.1', '1.0']:
        logger.error("Increment not 0.1 or 1.0")
        return
    else:
        increment = float(cond_action.do_action_string)

    change_in_duty_cycle = abs(cond_action.do_output_pwm - cond_action.do_output_pwm2)
    steps = change_in_duty_cycle * 1 / increment

    seconds_per_step = cond_action.do_output_duration / steps

    start_duty_cycle = cond_action.do_output_pwm
    end_duty_cycle = cond_action.do_output_pwm2
    current_duty_cycle = start_duty_cycle

    output_on = threading.Thread(
        target=control.output_on,
        args=(cond_action.do_unique_id,),
        kwargs={'duty_cycle': start_duty_cycle})
    output_on.start()

    loop_running = True
    timer = time.time() + seconds_per_step
    while True:
        if timer < time.time():
            while timer < time.time():
                timer += seconds_per_step
                if start_duty_cycle < end_duty_cycle:
                    current_duty_cycle += increment
                    if current_duty_cycle > end_duty_cycle:
                        current_duty_cycle = end_duty_cycle
                        loop_running = False
                else:
                    current_duty_cycle -= increment
                    if current_duty_cycle < end_duty_cycle:
                        current_duty_cycle = end_duty_cycle
                        loop_running = False

            output_on = threading.Thread(
                target=control.output_on,
                args=(cond_action.do_unique_id,),
                kwargs={'duty_cycle': current_duty_cycle})
            output_on.start()

            if not loop_running:
                break
    return message


def action_command(cond_action, message):
    # Replace string variables with actual values
    command_str = cond_action.do_action_string

    # TODO: Maybe get this working again with the new measurement system
    # # Replace measurement variables
    # if last_measurement:
    #     command_str = command_str.replace(
    #         "((measure_{var}))".format(
    #             var=device_measurement), str(last_measurement))
    # if device and device.period:
    #     command_str = command_str.replace(
    #         "((measure_period))", str(device.period))
    # if input_dev:
    #     command_str = command_str.replace(
    #         "((measure_location))", str(input_dev.location))
    # if input_dev and device_measurement == input_dev.measurements:
    #     command_str = command_str.replace(
    #         "((measure_linux_command))", str(last_measurement))
    #
    # # Replace output variables
    # if output:
    #     if output.pin:
    #         command_str = command_str.replace(
    #             "((output_pin))", str(output.pin))
    #     if output_state:
    #         command_str = command_str.replace(
    #             "((output_action))", str(output_state))
    #     if on_duration:
    #         command_str = command_str.replace(
    #             "((output_duration))", str(on_duration))
    #     if duty_cycle:
    #         command_str = command_str.replace(
    #             "((output_pwm))", str(duty_cycle))
    #
    # # Replace edge variables
    # if edge:
    #     command_str = command_str.replace(
    #         "((edge_state))", str(edge))

    message += " Execute '{com}' ".format(
        com=command_str)

    _, _, cmd_status = cmd_output(command_str)

    message += "(return status: {stat}).".format(stat=cmd_status)
    return message


def action_create_note(cond_action, message, single_action, note_tags):
    tag_name = db_retrieve_table_daemon(
        NoteTags, unique_id=cond_action.do_action_string).name

    message += " Create note with tag '{}'.".format(tag_name)
    if single_action and cond_action.do_action_string:
        list_tags = []
        check_tag = db_retrieve_table_daemon(
            NoteTags, unique_id=cond_action.do_action_string)
        if check_tag:
            list_tags.append(cond_action.do_action_string)

        if list_tags:
            with session_scope(MYCODO_DB_PATH) as db_session:
                new_note = Notes()
                new_note.name = 'Action'
                new_note.tags = ','.join(list_tags)
                new_note.note = message
                db_session.add(new_note)
    else:
        note_tags.append(cond_action.do_action_string)
    return message, note_tags


def action_photo(cond_action, message):
    this_camera = db_retrieve_table_daemon(
        Camera, unique_id=cond_action.do_unique_id, entry='first')
    message += "  Capturing photo with camera {unique_id} ({id}, {name}).".format(
        unique_id=cond_action.do_unique_id,
        id=this_camera.id,
        name=this_camera.name)
    camera_still = db_retrieve_table_daemon(
        Camera, unique_id=cond_action.do_unique_id)
    attachment_path_file = camera_record('photo', camera_still.unique_id)
    attachment_file = os.path.join(attachment_path_file[0], attachment_path_file[1])
    return message, attachment_file


def action_video(cond_action, message):
    this_camera = db_retrieve_table_daemon(
        Camera, unique_id=cond_action.do_unique_id, entry='first')
    message += "  Capturing video with camera {unique_id} ({id}, {name}).".format(
        unique_id=cond_action.do_unique_id,
        id=this_camera.id,
        name=this_camera.name)
    camera_stream = db_retrieve_table_daemon(
        Camera, unique_id=cond_action.do_unique_id)
    attachment_path_file = camera_record(
        'video', camera_stream.unique_id,
        duration_sec=cond_action.do_camera_duration)
    attachment_file = os.path.join(attachment_path_file[0], attachment_path_file[1])
    return message, attachment_file


def action_email(logger_actions,
                 cond_action,
                 message,
                 single_action,
                 attachment_file,
                 email_recipients,
                 attachment_type):
    message += " Notify {email}.".format(
        email=cond_action.do_action_string)
    # attachment_type != False indicates to
    # attach a photo or video
    if cond_action.action_type == 'photo_email':
        message += " Photo attached to email."
        attachment_type = 'still'
    elif cond_action.action_type == 'video_email':
        message += " Video attached to email."
        attachment_type = 'video'

    if single_action:
        # If the emails per hour limit has not been exceeded
        smtp_wait_timer, allowed_to_send_notice = check_allowed_to_email()
        if allowed_to_send_notice and cond_action.do_action_string:
            smtp = db_retrieve_table_daemon(SMTP, entry='first')
            send_email(smtp.host, smtp.ssl, smtp.port,
                       smtp.user, smtp.passw, smtp.email_from,
                       [cond_action.do_action_string], message,
                       attachment_file, attachment_type)
        else:
            logger_actions.error(
                "Wait {sec:.0f} seconds to email again.".format(
                    sec=smtp_wait_timer - time.time()))
    else:
        email_recipients.append(cond_action.do_action_string)

    # Email the Conditional message to multiple recipients
    # Optionally capture a photo or video and attach to the email.
    if cond_action.action_type in ['email_multiple']:

        message += " Notify {email}.".format(
            email=cond_action.do_action_string)
        # attachment_type != False indicates to
        # attach a photo or video
        if cond_action.action_type == 'photo_email':
            message += " Photo attached to email."
            attachment_type = 'still'
        elif cond_action.action_type == 'video_email':
            message += " Video attached to email."
            attachment_type = 'video'

        if single_action:
            # If the emails per hour limit has not been exceeded
            smtp_wait_timer, allowed_to_send_notice = check_allowed_to_email()
            if allowed_to_send_notice and cond_action.do_action_string:
                smtp = db_retrieve_table_daemon(SMTP, entry='first')
                send_email(smtp.host, smtp.ssl, smtp.port,
                           smtp.user, smtp.passw, smtp.email_from,
                           cond_action.do_action_string.split(','), message,
                           attachment_file, attachment_type)
            else:
                logger.error(
                    "Wait {sec:.0f} seconds to email again.".format(
                        sec=smtp_wait_timer - time.time()))
        else:
            email_recipients.extend(cond_action.do_action_string.split(','))
    return message, email_recipients, attachment_type


def action_activate_controller(cond_action, message):
    control = DaemonControl()
    (controller_type,
     controller_object,
     controller_entry) = which_controller(
        cond_action.do_unique_id)
    message += " Activate Controller {unique_id} ({id}, {name}).".format(
        unique_id=cond_action.do_unique_id,
        id=controller_entry.id,
        name=controller_entry.name)
    if controller_entry.is_activated:
        message += " Notice: Controller is already active!"
    else:
        with session_scope(MYCODO_DB_PATH) as new_session:
            mod_cont = new_session.query(controller_object).filter(
                controller_object.unique_id == cond_action.do_unique_id).first()
            mod_cont.is_activated = True
            new_session.commit()
        activate_controller = threading.Thread(
            target=control.controller_activate,
            args=(controller_type,
                  cond_action.do_unique_id,))
        activate_controller.start()
    return message


def action_deactivate_controller(cond_action, message):
    control = DaemonControl()
    (controller_type,
     controller_object,
     controller_entry) = which_controller(
        cond_action.do_unique_id)
    message += " Deactivate Controller {unique_id} ({id}, {name}).".format(
        unique_id=cond_action.do_unique_id,
        id=controller_entry.id,
        name=controller_entry.name)
    if not controller_entry.is_activated:
        message += " Notice: Controller is already inactive!"
    else:
        with session_scope(MYCODO_DB_PATH) as new_session:
            mod_cont = new_session.query(controller_object).filter(
                controller_object.unique_id == cond_action.do_unique_id).first()
            mod_cont.is_activated = False
            new_session.commit()
        deactivate_controller = threading.Thread(
            target=control.controller_deactivate,
            args=(controller_type,
                  cond_action.do_unique_id,))
        deactivate_controller.start()
    return message


def action_resume_pid(cond_action, message):
    control = DaemonControl()
    pid = db_retrieve_table_daemon(
        PID, unique_id=cond_action.do_unique_id, entry='first')
    message += " Resume PID {unique_id} ({id}, {name}).".format(
        unique_id=cond_action.do_unique_id,
        id=pid.id,
        name=pid.name)
    if not pid.is_paused:
        message += " Notice: PID is not paused!"
    elif pid.is_activated:
        with session_scope(MYCODO_DB_PATH) as new_session:
            mod_pid = new_session.query(PID).filter(
                PID.unique_id == cond_action.do_unique_id).first()
            mod_pid.is_paused = False
            new_session.commit()
        resume_pid = threading.Thread(
            target=control.pid_resume,
            args=(cond_action.do_unique_id,))
        resume_pid.start()
    return message


def action_pause_pid(cond_action, message):
    control = DaemonControl()
    pid = db_retrieve_table_daemon(
        PID, unique_id=cond_action.do_unique_id, entry='first')
    message += " Pause PID {unique_id} ({id}, {name}).".format(
        unique_id=cond_action.do_unique_id,
        id=pid.id,
        name=pid.name)
    if pid.is_paused:
        message += " Notice: PID is already paused!"
    elif pid.is_activated:
        with session_scope(MYCODO_DB_PATH) as new_session:
            mod_pid = new_session.query(PID).filter(
                PID.unique_id == cond_action.do_unique_id).first()
            mod_pid.is_paused = True
            new_session.commit()
        pause_pid = threading.Thread(
            target=control.pid_pause,
            args=(cond_action.do_unique_id,))
        pause_pid.start()
    return message


def action_setpoint_pid(cond_action, message):
    control = DaemonControl()
    pid = db_retrieve_table_daemon(
        PID, unique_id=cond_action.do_unique_id, entry='first')
    message += " Set Setpoint of PID {unique_id} ({id}, {name}).".format(
        unique_id=cond_action.do_unique_id,
        id=pid.id,
        name=pid.name)
    if pid.is_activated:
        setpoint_pid = threading.Thread(
            target=control.pid_set,
            args=(pid.unique_id,
                  'setpoint',
                  float(cond_action.do_action_string),))
        setpoint_pid.start()
    else:
        with session_scope(MYCODO_DB_PATH) as new_session:
            mod_pid = new_session.query(PID).filter(
                PID.unique_id == cond_action.do_unique_id).first()
            mod_pid.setpoint = float(cond_action.do_action_string)
            new_session.commit()
    return message


def action_setpoint_pid_raise(cond_action, message):
    control = DaemonControl()
    pid = db_retrieve_table_daemon(
        PID, unique_id=cond_action.do_unique_id, entry='first')
    new_setpoint = pid.setpoint + float(cond_action.do_action_string)
    message += " Raise Setpoint of PID {unique_id} by {amt}, to {sp} ({id}, {name}).".format(
        unique_id=cond_action.do_unique_id,
        amt=float(cond_action.do_action_string),
        sp=new_setpoint,
        id=pid.id,
        name=pid.name)
    if pid.is_activated:
        setpoint_pid = threading.Thread(
            target=control.pid_set,
            args=(pid.unique_id,
                  'setpoint',
                  new_setpoint,))
        setpoint_pid.start()
    else:
        with session_scope(MYCODO_DB_PATH) as new_session:
            mod_pid = new_session.query(PID).filter(
                PID.unique_id == cond_action.do_unique_id).first()
            mod_pid.setpoint = new_setpoint
            new_session.commit()
    return message


def action_setpoint_pid_lower(cond_action, message):
    control = DaemonControl()
    pid = db_retrieve_table_daemon(
        PID, unique_id=cond_action.do_unique_id, entry='first')
    new_setpoint = pid.setpoint - float(cond_action.do_action_string)
    message += " Lower Setpoint of PID {unique_id} by {amt}, to {sp} ({id}, {name}).".format(
        unique_id=cond_action.do_unique_id,
        amt=float(cond_action.do_action_string),
        sp=new_setpoint,
        id=pid.id,
        name=pid.name)
    if pid.is_activated:
        setpoint_pid = threading.Thread(
            target=control.pid_set,
            args=(pid.unique_id,
                  'setpoint',
                  new_setpoint,))
        setpoint_pid.start()
    else:
        with session_scope(MYCODO_DB_PATH) as new_session:
            mod_pid = new_session.query(PID).filter(
                PID.unique_id == cond_action.do_unique_id).first()
            mod_pid.setpoint = new_setpoint
            new_session.commit()
    return message


def action_method_pid(cond_action, message):
    control = DaemonControl()
    pid = db_retrieve_table_daemon(
        PID, unique_id=cond_action.do_unique_id, entry='first')
    message += " Set Method of PID {unique_id} ({id}, {name}).".format(
        unique_id=cond_action.do_unique_id,
        id=pid.id,
        name=pid.name)

    # Instruct method to start
    with session_scope(MYCODO_DB_PATH) as new_session:
        mod_pid = new_session.query(PID).filter(
            PID.unique_id == cond_action.do_unique_id).first()
        mod_pid.method_start_time = 'Ready'
        new_session.commit()

    pid = db_retrieve_table_daemon(
        PID, unique_id=cond_action.do_unique_id, entry='first')
    if pid.is_activated:
        method_pid = threading.Thread(
            target=control.pid_set,
            args=(pid.unique_id,
                  'method',
                  cond_action.do_action_string,))
        method_pid.start()
    else:
        with session_scope(MYCODO_DB_PATH) as new_session:
            mod_pid = new_session.query(PID).filter(
                PID.unique_id == cond_action.do_unique_id).first()
            mod_pid.method_id = cond_action.do_action_string
            new_session.commit()
    return message


def action_flash_lcd_on(cond_action, message):
    control = DaemonControl()
    lcd = db_retrieve_table_daemon(
        LCD, unique_id=cond_action.do_unique_id)
    message += " LCD {unique_id} ({id}, {name}) Flash On.".format(
        unique_id=cond_action.do_unique_id,
        id=lcd.id,
        name=lcd.name)

    start_flashing = threading.Thread(
        target=control.lcd_flash,
        args=(cond_action.do_unique_id, True,))
    start_flashing.start()
    return message


def action_flash_lcd_off(cond_action, message):
    control = DaemonControl()
    lcd = db_retrieve_table_daemon(
        LCD, unique_id=cond_action.do_unique_id)
    message += " LCD {unique_id} ({id}, {name}) Flash Off.".format(
        unique_id=cond_action.do_unique_id,
        id=lcd.id,
        name=lcd.name)

    start_flashing = threading.Thread(
        target=control.lcd_flash,
        args=(cond_action.do_unique_id, False,))
    start_flashing.start()
    return message


def action_lcd_backlight_off(cond_action, message):
    control = DaemonControl()
    lcd = db_retrieve_table_daemon(
        LCD, unique_id=cond_action.do_unique_id)
    message += " LCD {unique_id} ({id}, {name}) Backlight Off.".format(
        unique_id=cond_action.do_unique_id,
        id=lcd.id,
        name=lcd.name)

    start_flashing = threading.Thread(
        target=control.lcd_backlight,
        args=(cond_action.do_unique_id, False,))
    start_flashing.start()
    return message


def action_lcd_backlight_on(cond_action, message):
    control = DaemonControl()
    lcd = db_retrieve_table_daemon(
        LCD, unique_id=cond_action.do_unique_id)
    message += " LCD {unique_id} ({id}, {name}) Backlight On.".format(
        unique_id=cond_action.do_unique_id,
        id=lcd.id,
        name=lcd.name)

    start_flashing = threading.Thread(
        target=control.lcd_backlight,
        args=(cond_action.do_unique_id, True,))
    start_flashing.start()
    return message


def trigger_action(
        cond_action_id,
        message='',
        note_tags=None,
        email_recipients=None,
        attachment_file=None,
        attachment_type=None,
        single_action=False,
        debug=False):
    """
    Trigger individual action

    If single_action == False, message, note_tags, email_recipients,
    attachment_file, and attachment_type are returned and may be
    passed back to this function in order to append to those lists.

    :param cond_action_id: unique_id of action
    :param message: message string to append to that will be sent back
    :param note_tags: list of note tags to use if creating a note
    :param email_recipients: list of email addresses to notify if sending an email
    :param attachment_file: string location of a file to attach to an email
    :param attachment_type: string type of email attachment
    :param single_action: True if only one action is being triggered, False if only one of multiple actions
    :param debug: determine if logging level should be DEBUG

    :return: message or (message, note_tags, email_recipients, attachment_file, attachment_type)
    """
    cond_action = db_retrieve_table_daemon(Actions, unique_id=cond_action_id)
    if not cond_action:
        message += 'Error: Action with ID {} not found!'.format(
            cond_action_id)
        if single_action:
            return message
        else:
            return (message,
                    note_tags,
                    email_recipients,
                    attachment_file,
                    attachment_type)

    logger_actions = logging.getLogger("mycodo.trigger_action_{id}".format(
        id=cond_action.unique_id.split('-')[0]))

    if debug:
        logger_actions.setLevel(logging.DEBUG)
    else:
        logger_actions.setLevel(logging.INFO)

    message += "\n[Action {id}, {name}]:".format(
        id=cond_action.unique_id.split('-')[0],
        name=FUNCTION_ACTION_INFO[cond_action.action_type]['name'])

    try:
        if cond_action.action_type == 'pause_actions':
            message = action_pause(cond_action, message)
        elif cond_action.action_type == 'infrared_send':
            message = action_ir_send(cond_action, message)
        elif (cond_action.action_type == 'output' and
                cond_action.do_unique_id and
                cond_action.do_output_state in ['on', 'off']):
            message = action_output(cond_action, message)
        elif (cond_action.action_type == 'output_pwm' and
                cond_action.do_unique_id and
                0 <= cond_action.do_output_pwm <= 100):
            message = action_output_pwm(cond_action, message)
        elif (cond_action.action_type == 'output_ramp_pwm' and
                cond_action.do_unique_id and
                0 <= cond_action.do_output_pwm <= 100 and
                0 <= cond_action.do_output_pwm2 <= 100 and
                cond_action.do_output_duration > 0):
            message = action_output_ramp_pwm(cond_action, message)
        elif cond_action.action_type == 'command':
            message = action_command(cond_action, message)
        elif cond_action.action_type == 'create_note':
            message, note_tags = action_create_note(
                cond_action, message, single_action, note_tags)
        elif cond_action.action_type in ['photo', 'photo_email']:
            message, attachment_file = action_photo(cond_action, message)
        elif cond_action.action_type in ['video', 'video_email']:
            message, attachment_file = action_video(cond_action, message)
        elif cond_action.action_type in ['email',
                                         'photo_email',
                                         'video_email']:
            message, email_recipients, attachment_type = action_email(
                logger_actions,
                cond_action,
                message,
                single_action,
                attachment_file,
                email_recipients,
                attachment_type)
        elif cond_action.action_type == 'activate_controller':
            message = action_activate_controller(cond_action, message)
        elif cond_action.action_type == 'deactivate_controller':
            message = action_deactivate_controller(cond_action, message)
        elif cond_action.action_type == 'resume_pid':
            message = action_resume_pid(cond_action, message)
        elif cond_action.action_type == 'pause_pid':
            message = action_pause_pid(cond_action, message)
        elif cond_action.action_type == 'setpoint_pid':
            message = action_setpoint_pid(cond_action, message)
        elif cond_action.action_type == 'setpoint_pid_raise':
            message = action_setpoint_pid_raise(cond_action, message)
        elif cond_action.action_type == 'setpoint_pid_lower':
            message = action_setpoint_pid_lower(cond_action, message)
        elif cond_action.action_type == 'method_pid':
            message = action_method_pid(cond_action, message)
        elif cond_action.action_type == 'flash_lcd_on':
            message = action_flash_lcd_on(cond_action, message)
        elif cond_action.action_type == 'flash_lcd_off':
            message = action_flash_lcd_off(cond_action, message)
        elif cond_action.action_type == 'lcd_backlight_off':
            message = action_lcd_backlight_off(cond_action, message)
        elif cond_action.action_type == 'lcd_backlight_on':
            message = action_lcd_backlight_on(cond_action, message)

    except Exception:
        logger_actions.exception("Error triggering action:")
        message += " Error while executing action! " \
                   "See Daemon log for details."

    logger_actions.debug("Message: {}".format(message))
    logger_actions.debug("Note Tags: {}".format(note_tags))
    logger_actions.debug("Email Recipients: {}".format(email_recipients))
    logger_actions.debug("Attachment Files: {}".format(attachment_file))
    logger_actions.debug("Attachment Type: {}".format(attachment_type))

    if single_action:
        return message
    else:
        return (message, note_tags, email_recipients,
                attachment_file, attachment_type)


def trigger_function_actions(function_id, message='', debug=False):
    """
    Execute the Actions belonging to a particular Function

    :param function_id:
    :param message: The message generated from the conditional check
    :param debug: determine if logging level should be DEBUG
    :return:
    """
    logger_actions = logging.getLogger(
        "mycodo.trigger_function_actions_{id}".format(
            id=function_id.split('-')[0]))

    if debug:
        logger_actions.setLevel(logging.DEBUG)
    else:
        logger_actions.setLevel(logging.INFO)

    # List of all email notification recipients
    # List is appended with TO email addresses when an email Action is
    # encountered. An email is sent to all recipients after all actions
    # have been executed.
    email_recipients = []

    # List of tags to add to a note
    note_tags = []

    attachment_file = None
    attachment_type = None

    actions = db_retrieve_table_daemon(Actions)
    actions = actions.filter(
        Actions.function_id == function_id).all()

    for cond_action in actions:
        (message,
         note_tags,
         email_recipients,
         attachment_file,
         attachment_type) = trigger_action(
            cond_action.unique_id,
            message=message,
            single_action=False,
            note_tags=note_tags,
            email_recipients=email_recipients,
            attachment_file=attachment_file,
            attachment_type=attachment_type,
            debug=debug)

    # Send email after all conditional actions have been checked
    # In order to append all action messages to send in the email
    # send_email_at_end will be None or the TO email address
    if email_recipients:
        # If the emails per hour limit has not been exceeded
        smtp_wait_timer, allowed_to_send_notice = check_allowed_to_email()
        if allowed_to_send_notice:
            smtp = db_retrieve_table_daemon(SMTP, entry='first')
            send_email(smtp.host, smtp.ssl, smtp.port,
                       smtp.user, smtp.passw, smtp.email_from,
                       email_recipients, message,
                       attachment_file, attachment_type)
        else:
            logger_actions.error(
                "Wait {sec:.0f} seconds to email again.".format(
                    sec=smtp_wait_timer - time.time()))

    # Create a note with the tags from the unique_ids in the list note_tags
    if note_tags:
        list_tags = []
        for each_note_tag_id in note_tags:
            check_tag = db_retrieve_table_daemon(
                NoteTags, unique_id=each_note_tag_id)
            if check_tag:
                list_tags.append(each_note_tag_id)
        if list_tags:
            with session_scope(MYCODO_DB_PATH) as db_session:
                new_note = Notes()
                new_note.name = 'Action'
                new_note.tags = ','.join(list_tags)
                new_note.note = message
                db_session.add(new_note)

    logger_actions.debug("Message: {}".format(message))


def which_controller(unique_id):
    """Determine which type of controller the unique_id is for"""
    controller_type = None
    controller_object = None
    controller_entry = None
    if db_retrieve_table_daemon(Conditional, unique_id=unique_id):
        controller_type = 'Conditional'
        controller_object = Conditional
        controller_entry = db_retrieve_table_daemon(
            Conditional, unique_id=unique_id)
    elif db_retrieve_table_daemon(Input, unique_id=unique_id):
        controller_type = 'Input'
        controller_object = Input
        controller_entry = db_retrieve_table_daemon(
            Input, unique_id=unique_id)
    elif db_retrieve_table_daemon(LCD, unique_id=unique_id):
        controller_type = 'LCD'
        controller_object = LCD
        controller_entry = db_retrieve_table_daemon(
            LCD, unique_id=unique_id)
    elif db_retrieve_table_daemon(Math, unique_id=unique_id):
        controller_type = 'Math'
        controller_object = Math
        controller_entry = db_retrieve_table_daemon(
            Math, unique_id=unique_id)
    elif db_retrieve_table_daemon(PID, unique_id=unique_id):
        controller_type = 'PID'
        controller_object = PID
        controller_entry = db_retrieve_table_daemon(
            PID, unique_id=unique_id)
    elif db_retrieve_table_daemon(Trigger, unique_id=unique_id):
        controller_type = 'Trigger'
        controller_object = Trigger
        controller_entry = db_retrieve_table_daemon(
            Trigger, unique_id=unique_id)
    return controller_type, controller_object, controller_entry
