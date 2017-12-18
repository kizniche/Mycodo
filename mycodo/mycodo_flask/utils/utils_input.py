# -*- coding: utf-8 -*-
import logging
import os
import sqlalchemy

from flask import flash
from flask import redirect
from flask import url_for

from mycodo.mycodo_flask.extensions import db
from flask_babel import gettext
from RPi import GPIO

from mycodo.mycodo_client import DaemonControl

from mycodo.databases.models import Conditional
from mycodo.databases.models import ConditionalActions
from mycodo.databases.models import DisplayOrder
from mycodo.databases.models import PID
from mycodo.databases.models import Input
from mycodo.utils.system_pi import csv_to_list_of_int
from mycodo.utils.system_pi import list_to_csv

from mycodo.mycodo_flask.utils.utils_general import add_display_order
from mycodo.mycodo_flask.utils.utils_general import controller_activate_deactivate
from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.mycodo_flask.utils.utils_general import flash_form_errors
from mycodo.mycodo_flask.utils.utils_general import flash_success_errors
from mycodo.mycodo_flask.utils.utils_general import reorder

from mycodo.config import DEVICES_DEFAULT_LOCATION

logger = logging.getLogger(__name__)


#
# Input manipulation
#

def input_add(form_add_sensor):
    action = u'{action} {controller}'.format(
        action=gettext(u"Add"),
        controller=gettext(u"Input"))
    error = []

    if form_add_sensor.validate():
        for _ in range(0, form_add_sensor.numberSensors.data):
            new_sensor = Input()
            new_sensor.device = form_add_sensor.sensor.data
            new_sensor.name = '{name} Input'.format(name=form_add_sensor.sensor.data)
            if GPIO.RPI_INFO['P1_REVISION'] in [2, 3]:
                new_sensor.i2c_bus = 1
                new_sensor.multiplexer_bus = 1
            else:
                new_sensor.i2c_bus = 0
                new_sensor.multiplexer_bus = 0

            # Linux command as sensor
            if form_add_sensor.sensor.data == 'LinuxCommand':
                new_sensor.cmd_command = 'shuf -i 50-70 -n 1'
                new_sensor.cmd_measurement = 'Condition'
                new_sensor.cmd_measurement_units = 'unit'

            # Process monitors
            elif form_add_sensor.sensor.data == 'MYCODO_RAM':
                new_sensor.measurements = 'disk_space'
                new_sensor.location = 'Mycodo_daemon'
            elif form_add_sensor.sensor.data == 'RPi':
                new_sensor.measurements = 'temperature'
                new_sensor.location = 'RPi'
            elif form_add_sensor.sensor.data == 'RPiCPULoad':
                new_sensor.measurements = 'cpu_load_1m,' \
                                          'cpu_load_5m,' \
                                          'cpu_load_15m'
                new_sensor.location = 'RPi'
            elif form_add_sensor.sensor.data == 'RPiFreeSpace':
                new_sensor.measurements = 'disk_space'
                new_sensor.location = '/'
            elif form_add_sensor.sensor.data == 'EDGE':
                new_sensor.measurements = 'edge'

            # Signal measuremnt (PWM and RPM)
            elif form_add_sensor.sensor.data == 'SIGNAL_PWM':
                new_sensor.measurements = 'frequency,pulse_width,duty_cycle'
            elif form_add_sensor.sensor.data == 'SIGNAL_RPM':
                new_sensor.measurements = 'rpm'

            # Environmental Inputs
            # Temperature
            elif form_add_sensor.sensor.data in ['ATLAS_PT1000_I2C',
                                                 'ATLAS_PT1000_UART',
                                                 'DS18B20',
                                                 'TMP006']:
                new_sensor.measurements = 'temperature'
                if form_add_sensor.sensor.data == 'ATLAS_PT1000_I2C':
                    new_sensor.interface = 'I2C'
                    new_sensor.location = '0x66'
                elif form_add_sensor.sensor.data == 'ATLAS_PT1000_UART':
                    new_sensor.location = 'Tx/Rx'
                    new_sensor.interface = 'UART'
                    new_sensor.baud_rate = 9600
                    if GPIO.RPI_INFO['P1_REVISION'] == 3:
                        new_sensor.device_loc = "/dev/ttyS0"
                    else:
                        new_sensor.device_loc = "/dev/ttyAMA0"
                elif form_add_sensor.sensor.data == 'TMP006':
                    new_sensor.measurements = 'temperature_object,' \
                                              'temperature_die'
                    new_sensor.location = '0x40'

            # Temperature/Humidity
            elif form_add_sensor.sensor.data in ['AM2315', 'DHT11',
                                                 'DHT22', 'HTU21D',
                                                 'SHT1x_7x', 'SHT2x']:
                new_sensor.measurements = 'temperature,humidity,dewpoint'
                if form_add_sensor.sensor.data == 'AM2315':
                    new_sensor.location = '0x5c'
                elif form_add_sensor.sensor.data == 'HTU21D':
                    new_sensor.location = '0x40'
                elif form_add_sensor.sensor.data == 'SHT2x':
                    new_sensor.location = '0x40'

            # Chirp moisture sensor
            elif form_add_sensor.sensor.data == 'CHIRP':
                new_sensor.measurements = 'lux,moisture,temperature'
                new_sensor.location = '0x20'

            # CO2
            elif form_add_sensor.sensor.data == 'MH_Z16_I2C':
                new_sensor.measurements = 'co2'
                new_sensor.location = '0x63'
                new_sensor.interface = 'I2C'
            elif form_add_sensor.sensor.data in ['K30_UART',
                                                 'MH_Z16_UART',
                                                 'MH_Z19_UART']:
                new_sensor.measurements = 'co2'
                new_sensor.location = 'Tx/Rx'
                new_sensor.interface = 'UART'
                new_sensor.baud_rate = 9600
                if GPIO.RPI_INFO['P1_REVISION'] == 3:
                    new_sensor.device_loc = "/dev/ttyS0"
                else:
                    new_sensor.device_loc = "/dev/ttyAMA0"

            # pH
            elif form_add_sensor.sensor.data == 'ATLAS_PH_I2C':
                new_sensor.measurements = 'ph'
                new_sensor.location = '0x63'
                new_sensor.interface = 'I2C'
            elif form_add_sensor.sensor.data == 'ATLAS_PH_UART':
                new_sensor.measurements = 'ph'
                new_sensor.location = 'Tx/Rx'
                new_sensor.interface = 'UART'
                new_sensor.baud_rate = 9600
                if GPIO.RPI_INFO['P1_REVISION'] == 3:
                    new_sensor.device_loc = "/dev/ttyS0"
                else:
                    new_sensor.device_loc = "/dev/ttyAMA0"

            # Pressure
            elif form_add_sensor.sensor.data in ['BME280',
                                                 'BMP180',
                                                 'BMP280']:
                if form_add_sensor.sensor.data == 'BME280':
                    new_sensor.measurements = 'temperature,humidity,' \
                                              'dewpoint,pressure,altitude'
                    new_sensor.location = '0x76'
                elif form_add_sensor.sensor.data in ['BMP180', 'BMP280']:
                    new_sensor.measurements = 'temperature,pressure,altitude'
                    new_sensor.location = '0x77'

            # Light
            elif form_add_sensor.sensor.data in ['BH1750', 'TSL2561', 'TSL2591']:
                new_sensor.measurements = 'lux'
                if form_add_sensor.sensor.data == 'BH1750':
                    new_sensor.location = '0x23'
                    new_sensor.resolution = 0  # 0=Low, 1=High, 2=High2
                    new_sensor.sensitivity = 69
                elif form_add_sensor.sensor.data == 'TSL2561':
                    new_sensor.location = '0x39'
                elif form_add_sensor.sensor.data == 'TSL2591':
                    new_sensor.location = '0x29'

            # Analog to Digital Converters
            elif form_add_sensor.sensor.data in ['ADS1x15', 'MCP342x']:
                new_sensor.measurements = 'voltage'
                if form_add_sensor.sensor.data == 'ADS1x15':
                    new_sensor.location = '0x48'
                    new_sensor.adc_volts_min = -4.096
                    new_sensor.adc_volts_max = 4.096
                elif form_add_sensor.sensor.data == 'MCP342x':
                    new_sensor.location = '0x68'
                    new_sensor.adc_volts_min = -2.048
                    new_sensor.adc_volts_max = 2.048

            try:
                new_sensor.save()

                display_order = csv_to_list_of_int(
                    DisplayOrder.query.first().sensor)
                DisplayOrder.query.first().sensor = add_display_order(
                    display_order, new_sensor.id)
                db.session.commit()

                flash(gettext(
                    u"%(type)s Input with ID %(id)s (%(uuid)s) successfully added",
                    type=form_add_sensor.sensor.data,
                    id=new_sensor.id,
                    uuid=new_sensor.unique_id),
                      "success")
            except sqlalchemy.exc.OperationalError as except_msg:
                error.append(except_msg)
            except sqlalchemy.exc.IntegrityError as except_msg:
                error.append(except_msg)
        flash_success_errors(error, action, url_for('page_routes.page_input'))
    else:
        flash_form_errors(form_add_sensor)


def input_mod(form_mod_sensor):
    action = u'{action} {controller}'.format(
        action=gettext(u"Modify"),
        controller=gettext(u"Input"))
    error = []

    try:
        mod_sensor = Input.query.filter(
            Input.id == form_mod_sensor.modSensor_id.data).first()

        if mod_sensor.is_activated:
            error.append(gettext(
                u"Deactivate sensor controller before modifying its "
                u"settings"))
        if (mod_sensor.device == 'AM2315' and
                form_mod_sensor.period.data < 7):
            error.append(gettext(
                u"Choose a Read Period equal to or greater than 7. The "
                u"AM2315 may become unresponsive if the period is "
                u"below 7."))
        if ((form_mod_sensor.period.data < mod_sensor.pre_relay_duration) and
                mod_sensor.pre_relay_duration):
            error.append(gettext(
                u"The Read Period cannot be less than the Pre Output "
                u"Duration"))
        if (form_mod_sensor.device_loc.data and
                not os.path.exists(form_mod_sensor.device_loc.data)):
            error.append(gettext(
                u"Invalid device or improper permissions to read device"))

        if not error:
            mod_sensor.name = form_mod_sensor.name.data
            mod_sensor.i2c_bus = form_mod_sensor.i2c_bus.data
            if form_mod_sensor.location.data:
                mod_sensor.location = form_mod_sensor.location.data
            if form_mod_sensor.power_relay_id.data:
                mod_sensor.power_relay_id = form_mod_sensor.power_relay_id.data
            else:
                mod_sensor.power_relay_id = None
            if form_mod_sensor.baud_rate.data:
                mod_sensor.baud_rate = form_mod_sensor.baud_rate.data
            if form_mod_sensor.device_loc.data:
                mod_sensor.device_loc = form_mod_sensor.device_loc.data
            if form_mod_sensor.pre_relay_id.data:
                mod_sensor.pre_relay_id = form_mod_sensor.pre_relay_id.data
            else:
                mod_sensor.pre_relay_id = None
            mod_sensor.pre_relay_duration = form_mod_sensor.pre_relay_duration.data
            mod_sensor.period = form_mod_sensor.period.data
            mod_sensor.resolution = form_mod_sensor.resolution.data
            mod_sensor.sensitivity = form_mod_sensor.sensitivity.data
            mod_sensor.calibrate_sensor_measure = form_mod_sensor.calibrate_sensor_measure.data
            mod_sensor.cmd_command = form_mod_sensor.cmd_command.data
            mod_sensor.cmd_measurement = form_mod_sensor.cmd_measurement.data
            mod_sensor.cmd_measurement_units = form_mod_sensor.cmd_measurement_units.data
            # Multiplexer options
            mod_sensor.multiplexer_address = form_mod_sensor.multiplexer_address.data
            mod_sensor.multiplexer_bus = form_mod_sensor.multiplexer_bus.data
            mod_sensor.multiplexer_channel = form_mod_sensor.multiplexer_channel.data
            # ADC options
            mod_sensor.adc_channel = form_mod_sensor.adc_channel.data
            mod_sensor.adc_gain = form_mod_sensor.adc_gain.data
            mod_sensor.adc_resolution = form_mod_sensor.adc_resolution.data
            mod_sensor.adc_measure = form_mod_sensor.adc_measurement.data.replace(" ", "_")
            mod_sensor.adc_measure_units = form_mod_sensor.adc_measurement_units.data
            mod_sensor.adc_volts_min = form_mod_sensor.adc_volts_min.data
            mod_sensor.adc_volts_max = form_mod_sensor.adc_volts_max.data
            mod_sensor.adc_units_min = form_mod_sensor.adc_units_min.data
            mod_sensor.adc_units_max = form_mod_sensor.adc_units_max.data
            mod_sensor.adc_inverse_unit_scale = form_mod_sensor.adc_inverse_unit_scale.data
            # Switch options
            mod_sensor.switch_edge = form_mod_sensor.switch_edge.data
            mod_sensor.switch_bouncetime = form_mod_sensor.switch_bounce_time.data
            mod_sensor.switch_reset_period = form_mod_sensor.switch_reset_period.data
            # PWM and RPM options
            mod_sensor.weighting = form_mod_sensor.weighting.data
            mod_sensor.rpm_pulses_per_rev = form_mod_sensor.rpm_pulses_per_rev.data
            mod_sensor.sample_time = form_mod_sensor.sample_time.data
            # SHT sensor options
            if form_mod_sensor.sht_clock_pin.data:
                mod_sensor.sht_clock_pin = form_mod_sensor.sht_clock_pin.data
            if form_mod_sensor.sht_voltage.data:
                mod_sensor.sht_voltage = form_mod_sensor.sht_voltage.data
            db.session.commit()
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('page_routes.page_input'))


def input_del(form_mod_sensor):
    action = u'{action} {controller}'.format(
        action=gettext(u"Delete"),
        controller=gettext(u"Input"))
    error = []

    input_id = form_mod_sensor.modSensor_id.data

    try:
        input_dev = Input.query.filter(
            Input.id == input_id).first()
        if input_dev.is_activated:
            input_deactivate_associated_controllers(input_id)
            controller_activate_deactivate('deactivate', 'Input', input_id)

        # Delete any conditionals associated with the controller
        conditionals = Conditional.query.filter(
            Conditional.sensor_id == input_id).all()
        for each_cond in conditionals:
            conditional_actions = ConditionalActions.query.filter(
                ConditionalActions.conditional_id == each_cond.id).all()
            for each_cond_action in conditional_actions:
                db.session.delete(each_cond_action)
            db.session.delete(each_cond)
        db.session.commit()

        delete_entry_with_id(Input, input_id)
        try:
            display_order = csv_to_list_of_int(DisplayOrder.query.first().sensor)
            display_order.remove(int(input_id))
            DisplayOrder.query.first().sensor = list_to_csv(display_order)
        except Exception:  # id not in list
            pass
        db.session.commit()
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('page_routes.page_input'))


def input_reorder(input_id, display_order, direction):
    action = u'{action} {controller}'.format(
        action=gettext(u"Reorder"),
        controller=gettext(u"Input"))
    error = []

    try:
        status, reord_list = reorder(display_order, input_id, direction)
        if status == 'success':
            DisplayOrder.query.first().sensor = ','.join(map(str, reord_list))
            db.session.commit()
        elif status == 'error':
            error.append(reord_list)
    except Exception as except_msg:
        error.append(except_msg)
    flash_success_errors(error, action, url_for('page_routes.page_input'))


def input_activate(form_mod_sensor):
    input_id = form_mod_sensor.modSensor_id.data
    input_dev = Input.query.filter(Input.id == input_id).first()
    if (input_dev.device != u'LinuxCommand' and
            not input_dev.location and
            input_dev.device not in DEVICES_DEFAULT_LOCATION):
        flash("Cannot activate Input without the GPIO/I2C Address/Port "
              "to communicate with it set.", "error")
        return redirect(url_for('page_routes.page_input'))
    elif (input_dev.device == u'LinuxCommand' and
          input_dev.cmd_command is ''):
        flash("Cannot activate Input without a command set.", "error")
        return redirect(url_for('page_routes.page_input'))
    controller_activate_deactivate('activate', 'Input',  input_id)


def input_deactivate(form_mod_sensor):
    input_id = form_mod_sensor.modSensor_id.data
    input_deactivate_associated_controllers(input_id)
    controller_activate_deactivate('deactivate', 'Input', input_id)


# Deactivate any active PID or LCD controllers using this sensor
def input_deactivate_associated_controllers(input_id):
    # Deactivate any activated PIDs using this input
    sensor_unique_id = Input.query.filter(Input.id == input_id).first().unique_id
    pid = PID.query.filter(PID.is_activated == True).all()
    for each_pid in pid:
        if sensor_unique_id in each_pid.measurement:
            controller_activate_deactivate('deactivate',
                                           'PID',
                                           each_pid.id)


def check_refresh_conditional(input_id, cond_mod):
    sensor = (Input.query
              .filter(Input.id == input_id)
              .filter(Input.is_activated == True)
              ).first()
    if sensor:
        control = DaemonControl()
        control.refresh_input_conditionals(input_id, cond_mod)
