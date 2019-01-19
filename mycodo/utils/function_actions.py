# coding=utf-8
import logging
import threading
import time

import RPi.GPIO as GPIO

from mycodo.config import SQL_DATABASE_MYCODO
from mycodo.databases.models import Actions
from mycodo.databases.models import Camera
from mycodo.databases.models import Conditional
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
from mycodo.utils.send_data import send_email
from mycodo.utils.system_pi import cmd_output
from mycodo.utils.system_pi import return_measurement_info

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO

logger = logging.getLogger("mycodo.function_actions")


def get_condition_measurement(sql_condition):
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

    # Check Measurement Conditions
    if sql_condition.condition_type == 'measurement':
        # Check if there hasn't been a measurement in the last set number
        # of seconds. If not, trigger conditional
        last_measurement = get_last_measurement(
            device_id, unit, measurement, channel, max_age)
        return last_measurement

    # If the edge detection variable is set, calling this function will
    # trigger an edge detection event. This will merely produce the correct
    # message based on the edge detection settings.
    elif sql_condition.condition_type == 'gpio_state':
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(int(sql_condition.gpio_pin), GPIO.IN)
            gpio_state = GPIO.input(int(sql_condition.gpio_pin))
        except:
            gpio_state = None
            logger.error("Exception reading the GPIO pin")
        return gpio_state


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


def trigger_action(
        cond_action_id,
        message='',
        note_tags=None,
        email_recipients=None,
        attachment_file=None,
        attachment_type=None,
        single_action=False):
    cond_action = db_retrieve_table_daemon(Actions, unique_id=cond_action_id)
    if not cond_action:
        return

    logger_actions = logging.getLogger("mycodo.trigger_action_{id}".format(
        id=cond_action.unique_id.split('-')[0]))

    control = DaemonControl()

    smtp_table = db_retrieve_table_daemon(
        SMTP, entry='first')
    smtp_max_count = smtp_table.hourly_max
    smtp_wait_timer = smtp_table.smtp_wait_timer
    email_count = smtp_table.email_count

    message += "\n[Action {id}]:".format(
        id=cond_action.unique_id.split('-')[0], action_type=cond_action.action_type)

    # Pause
    if cond_action.action_type == 'pause_actions':
        message += " [{id}] Pause actions for {sec} seconds.".format(
            id=cond_action.id,
            sec=cond_action.pause_duration)

        time.sleep(cond_action.pause_duration)

    # Actuate output (duration)
    elif (cond_action.action_type == 'output' and cond_action.do_unique_id and
          cond_action.do_output_state in ['on', 'off']):
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
            kwargs={'duration': cond_action.do_output_duration})
        output_on_off.start()

    # Actuate output (PWM)
    elif (cond_action.action_type == 'output_pwm' and cond_action.do_unique_id and
          cond_action.do_output_pwm):
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

    # Execute command in shell
    elif cond_action.action_type == 'command':

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

    # Create Note
    elif cond_action.action_type == 'create_note':
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

    # Capture photo
    elif cond_action.action_type in ['photo', 'photo_email']:
        this_camera = db_retrieve_table_daemon(
            Camera, unique_id=cond_action.do_unique_id, entry='first')
        message += "  Capturing photo with camera {unique_id} ({id}, {name}).".format(
            unique_id=cond_action.do_unique_id,
            id=this_camera.id,
            name=this_camera.name)
        camera_still = db_retrieve_table_daemon(
            Camera, unique_id=cond_action.do_unique_id)
        attachment_file = camera_record('photo', camera_still.unique_id)

    # Capture video
    elif cond_action.action_type in ['video', 'video_email']:
        this_camera = db_retrieve_table_daemon(
            Camera, unique_id=cond_action.do_unique_id, entry='first')
        message += "  Capturing video with camera {unique_id} ({id}, {name}).".format(
            unique_id=cond_action.do_unique_id,
            id=this_camera.id,
            name=this_camera.name)
        camera_stream = db_retrieve_table_daemon(
            Camera, unique_id=cond_action.do_unique_id)
        attachment_file = camera_record(
            'video', camera_stream.unique_id,
            duration_sec=cond_action.do_camera_duration)

    # Activate Controller
    elif cond_action.action_type == 'activate_controller':
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
            # If controller is Conditional and is
            # run_pwm_method, activate method start
            is_conditional = db_retrieve_table_daemon(
                Conditional, unique_id=cond_action.do_unique_id, entry='first')
            if (is_conditional and
                    is_conditional.conditional_type == 'run_pwm_method'):
                with session_scope(MYCODO_DB_PATH) as new_session:
                    mod_cont_ready = new_session.query(Conditional).filter(
                        Conditional.unique_id == cond_action.do_unique_id).first()
                    mod_cont_ready.method_start_time = 'Ready'
                    new_session.commit()

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

    # Deactivate Controller
    elif cond_action.action_type == 'deactivate_controller':
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

    # Resume PID controller
    elif cond_action.action_type == 'resume_pid':
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

    # Pause PID controller
    elif cond_action.action_type == 'pause_pid':
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

    # Set PID Setpoint
    elif cond_action.action_type == 'setpoint_pid':
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
                mod_pid.setpoint = cond_action.do_action_string
                new_session.commit()

    # Set PID Method and start method from beginning
    elif cond_action.action_type == 'method_pid':
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

    # Email the Conditional message. Optionally capture a photo or
    # video and attach to the email.
    elif cond_action.action_type in ['email',
                                     'photo_email',
                                     'video_email']:

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

        # If the emails per hour limit has not been exceeded
        if allowed_to_send_notice:
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

            if single_action and cond_action.do_action_string:
                smtp = db_retrieve_table_daemon(SMTP, entry='first')
                send_email(smtp.host, smtp.ssl, smtp.port,
                           smtp.user, smtp.passw, smtp.email_from,
                           [cond_action.do_action_string], message,
                           attachment_file, attachment_type)
            else:
                email_recipients.append(cond_action.do_action_string)
        else:
            logger_actions.error(
                "Wait {sec:.0f} seconds to email again.".format(
                    sec=smtp_wait_timer - time.time()))

    elif cond_action.action_type == 'flash_lcd_on':
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

    elif cond_action.action_type == 'flash_lcd_off':
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

    elif cond_action.action_type == 'lcd_backlight_off':
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

    elif cond_action.action_type == 'lcd_backlight_on':
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

    if single_action:
        return message
    else:
        return message, note_tags, email_recipients, attachment_file, attachment_type


def trigger_function_actions(
        function_id,
        message='',
        last_measurement=None,
        device_id=None,
        device_measurement=None,
        edge=None,
        output_state=None,
        on_duration=None,
        duty_cycle=None):
    """
    Execute the Actions belonging to a particular Function

    :param function_id:
    :param device_id: The unique ID associated with the device_measurement
    :param message: The message generated from the conditional check
    :param last_measurement: The last measurement value
    :param device_measurement: The measurement (i.e. "temperature")
    :param edge: If edge conditional, rise/on (1) or fall/off (0)
    :param output_state: If output conditional, the output state (on/off) to trigger the action
    :param on_duration: If output conditional, the ON duration
    :param duty_cycle: If output conditional, the duty cycle
    :return:
    """
    logger_actions = logging.getLogger("mycodo.trigger_function_actions_{id}".format(
        id=function_id.split('-')[0]))

    # List of all email notification recipients
    # List is appended with TO email addresses when an email Action is
    # encountered. An email is sent to all recipients after all actions
    # have been executed.
    email_recipients = []

    # List of tags to add to a note
    note_tags = []

    attachment_file = None
    attachment_type = None
    input_dev = None
    output = None
    device = None

    actions = db_retrieve_table_daemon(Actions)
    actions = actions.filter(
        Actions.function_id == function_id).all()

    if device_id:
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

    for cond_action in actions:
        (message,
         note_tags,
         email_recipients,
         attachment_file,
         attachment_type) = trigger_action(cond_action.unique_id,
                                           message=message,
                                           single_action=False,
                                           note_tags=note_tags,
                                           email_recipients=email_recipients,
                                           attachment_file=attachment_file,
                                           attachment_type=attachment_type)

    # Send email after all conditional actions have been checked
    # In order to append all action messages to send in the email
    # send_email_at_end will be None or the TO email address
    if email_recipients:
        smtp = db_retrieve_table_daemon(SMTP, entry='first')
        send_email(smtp.host, smtp.ssl, smtp.port,
                   smtp.user, smtp.passw, smtp.email_from,
                   email_recipients, message,
                   attachment_file, attachment_type)

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

    logger_actions.debug(message)


def which_controller(unique_id):
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
