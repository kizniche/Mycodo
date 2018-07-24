# -*- coding: utf-8 -*-
import logging

import os
import re
import sqlalchemy
from RPi import GPIO
from flask import current_app
from flask import flash
from flask import redirect
from flask import url_for
from flask_babel import gettext

from mycodo.config import DEVICES_DEFAULT_LOCATION
from mycodo.config import LIST_DEVICES_ADC
from mycodo.config import LIST_DEVICES_SPI
from mycodo.config_devices_units import DEVICE_INFO
from mycodo.config_devices_units import MEASUREMENT_UNITS
from mycodo.databases.models import DisplayOrder
from mycodo.databases.models import Input
from mycodo.databases.models import PID
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.utils.utils_general import add_display_order
from mycodo.mycodo_flask.utils.utils_general import controller_activate_deactivate
from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.mycodo_flask.utils.utils_general import flash_form_errors
from mycodo.mycodo_flask.utils.utils_general import flash_success_errors
from mycodo.mycodo_flask.utils.utils_general import reorder
from mycodo.mycodo_flask.utils.utils_general import return_dependencies
from mycodo.utils.system_pi import csv_to_list_of_str
from mycodo.utils.system_pi import list_to_csv

logger = logging.getLogger(__name__)


#
# Input manipulation
#


def input_add(form_add):
    action = '{action} {controller}'.format(
        action=gettext("Add"),
        controller=gettext("Input"))
    error = []

    if current_app.config['TESTING']:
        unmet_deps = False
    else:
        unmet_deps = return_dependencies(form_add.input_type.data)
        if unmet_deps:
            error.append("The {dev} device you're trying to add has unmet dependencies: {dep}".format(
                dev=form_add.input_type.data, dep=unmet_deps))

    if form_add.validate():
        new_input = Input()
        new_input.device = form_add.input_type.data

        if GPIO.RPI_INFO['P1_REVISION'] in [2, 3]:
            new_input.i2c_bus = 1
        else:
            new_input.i2c_bus = 0

        if form_add.input_type.data in DEVICE_INFO:
            new_input.name = DEVICE_INFO[form_add.input_type.data]['name']
            new_input.measurements = ",".join(DEVICE_INFO[form_add.input_type.data]['measure'])
        else:
            new_input.name = 'Name'

        #
        # Set default values for new Inputs
        #

        # Set the default measurement values
        list_units = []
        for each_measurement in DEVICE_INFO[form_add.input_type.data]['measure']:
            if each_measurement in MEASUREMENT_UNITS:
                entry = '{measure},{unit}'.format(
                    measure=each_measurement,
                    unit=MEASUREMENT_UNITS[each_measurement]['units'][0])
                list_units.append(entry)
        new_input.convert_to_unit = ";".join(list_units)

        # Linux command as sensor
        if form_add.input_type.data == 'LinuxCommand':
            new_input.cmd_command = 'shuf -i 50-70 -n 1'
            new_input.cmd_measurement = 'Condition'
            new_input.cmd_measurement_units = 'unit'

        # Server is up or down
        elif form_add.input_type.data in ['SERVER_PING',
                                          'SERVER_PORT_OPEN']:
            new_input.location = '127.0.0.1'
            new_input.period = 3600

        # Process monitors
        elif form_add.input_type.data == 'MYCODO_RAM':
            new_input.location = 'Mycodo_daemon'
        elif form_add.input_type.data == 'RPi':
            new_input.location = 'RPi'
        elif form_add.input_type.data == 'RPiCPULoad':
            new_input.location = 'RPi'
        elif form_add.input_type.data == 'RPiFreeSpace':
            new_input.location = '/'

        # Environmental Inputs

        # Electrical Conductivity
        elif form_add.input_type.data == 'ATLAS_EC_I2C':
            new_input.location = '0x01'
            new_input.interface = 'I2C'
        elif form_add.input_type.data == 'ATLAS_EC_UART':
            new_input.location = 'Tx/Rx'
            new_input.interface = 'UART'
            new_input.baud_rate = 9600
            if GPIO.RPI_INFO['P1_REVISION'] == 3:
                new_input.device_loc = "/dev/ttyS0"
            else:
                new_input.device_loc = "/dev/ttyAMA0"

        # Temperature
        if form_add.input_type.data == 'TMP006':
            new_input.location = '0x40'
        elif form_add.input_type.data == 'ATLAS_PT1000_I2C':
            new_input.interface = 'I2C'
            new_input.location = '0x66'
        elif form_add.input_type.data == 'ATLAS_PT1000_UART':
            new_input.location = 'Tx/Rx'
            new_input.interface = 'UART'
            new_input.baud_rate = 9600
            if GPIO.RPI_INFO['P1_REVISION'] == 3:
                new_input.device_loc = "/dev/ttyS0"
            else:
                new_input.device_loc = "/dev/ttyAMA0"
        elif form_add.input_type.data in ['MAX31855',
                                          'MAX31856',
                                          'MAX31865']:
            new_input.pin_cs = 8
            new_input.pin_miso = 9
            new_input.pin_mosi = 10
            new_input.pin_clock = 11
            if form_add.input_type.data == 'MAX31856':
                new_input.thermocouple_type = 'K'
            elif form_add.input_type.data == 'MAX31865':
                new_input.thermocouple_type = 'PT100'
                new_input.ref_ohm = 0

        # Temperature/Humidity
        elif form_add.input_type.data in ['AM2315', 'DHT11', 'DHT22',
                                          'HDC1000', 'HTU21D', 'SHT1x_7x',
                                          'SHT2x']:
            if form_add.input_type.data == 'AM2315':
                new_input.location = '0x5c'
            elif form_add.input_type.data in ['HDC1000', 'HTU21D', 'SHT2x']:
                new_input.location = '0x40'
            if form_add.input_type.data =='HDC1000':
                new_input.resolution = 14
                new_input.resolution_2 = 14

        # Chirp moisture sensor
        elif form_add.input_type.data == 'CHIRP':
            new_input.location = '0x20'

        # CO2
        elif form_add.input_type.data == 'CCS811':
            new_input.location = '0x5B'
            new_input.interface = 'I2C'
        elif form_add.input_type.data == 'MH_Z16_I2C':
            new_input.location = '0x63'
            new_input.interface = 'I2C'
        elif form_add.input_type.data == 'K30_I2C':
            new_input.location = '0x68'
            new_input.interface = 'I2C'
        elif form_add.input_type.data in ['COZIR_CO2',
                                          'K30_UART',
                                          'MH_Z16_UART',
                                          'MH_Z19_UART']:
            new_input.location = 'Tx/Rx'
            new_input.interface = 'UART'
            new_input.baud_rate = 9600
            if GPIO.RPI_INFO['P1_REVISION'] == 3:
                new_input.device_loc = "/dev/ttyS0"
            else:
                new_input.device_loc = "/dev/ttyAMA0"

        # pH
        elif form_add.input_type.data == 'ATLAS_PH_I2C':
            new_input.location = '0x63'
            new_input.interface = 'I2C'
        elif form_add.input_type.data == 'ATLAS_PH_UART':
            new_input.location = 'Tx/Rx'
            new_input.interface = 'UART'
            new_input.baud_rate = 9600
            if GPIO.RPI_INFO['P1_REVISION'] == 3:
                new_input.device_loc = "/dev/ttyS0"
            else:
                new_input.device_loc = "/dev/ttyAMA0"

        # Pressure
        if form_add.input_type.data == 'BME280':
            new_input.location = '0x76'
        elif form_add.input_type.data in ['BMP180', 'BMP280']:
            new_input.location = '0x77'

        # Light
        elif form_add.input_type.data in ['BH1750',
                                          'TSL2561',
                                          'TSL2591']:
            if form_add.input_type.data == 'BH1750':
                new_input.location = '0x23'
                new_input.resolution = 0  # 0=Low, 1=High, 2=High2
                new_input.sensitivity = 69
            elif form_add.input_type.data == 'TSL2561':
                new_input.location = '0x39'
            elif form_add.input_type.data == 'TSL2591':
                new_input.location = '0x29'

        # Analog to Digital Converters
        elif form_add.input_type.data in LIST_DEVICES_ADC:
            new_input.adc_measure = 'Condition'
            new_input.adc_measure_units = 'units'
            new_input.convert_to_unit = 'voltage,volts'
            if form_add.input_type.data == 'ADS1x15':
                new_input.location = '0x48'
                new_input.adc_volts_min = -4.096
                new_input.adc_volts_max = 4.096
            elif form_add.input_type.data == 'MCP342x':
                new_input.location = '0x68'
                new_input.adc_volts_min = -2.048
                new_input.adc_volts_max = 2.048
            elif form_add.input_type.data == 'MCP3008':
                new_input.pin_cs = 8
                new_input.pin_miso = 9
                new_input.pin_mosi = 10
                new_input.pin_clock = 11
                new_input.adc_volts_min = 0
                new_input.adc_volts_max = 3.3

        try:
            if not error:
                new_input.save()

                display_order = csv_to_list_of_str(
                    DisplayOrder.query.first().inputs)
                DisplayOrder.query.first().inputs = add_display_order(
                    display_order, new_input.unique_id)
                db.session.commit()

                flash(gettext(
                    "%(type)s Input with ID %(id)s (%(uuid)s) successfully added",
                    type=form_add.input_type.data,
                    id=new_input.id,
                    uuid=new_input.unique_id),
                      "success")
        except sqlalchemy.exc.OperationalError as except_msg:
            error.append(except_msg)
        except sqlalchemy.exc.IntegrityError as except_msg:
            error.append(except_msg)

        flash_success_errors(error, action, url_for('routes_page.page_data'))
    else:
        flash_form_errors(form_add)

    if unmet_deps:
        return 1


def input_mod(form_mod, request_form):
    action = '{action} {controller}'.format(
        action=gettext("Modify"),
        controller=gettext("Input"))
    error = []

    try:
        mod_input = Input.query.filter(
            Input.unique_id == form_mod.input_id.data).first()

        if mod_input.is_activated:
            error.append(gettext(
                "Deactivate sensor controller before modifying its "
                "settings"))
        if (mod_input.device == 'AM2315' and
                form_mod.period.data < 7):
            error.append(gettext(
                "Choose a Read Period equal to or greater than 7. The "
                "AM2315 may become unresponsive if the period is "
                "below 7."))
        if (mod_input.device == 'LinuxCommand' and
                (form_mod.cmd_measurement.data == '' or
                 form_mod.cmd_measurement_units.data == '')):
            error.append(gettext(
                "Both a measurement and unit must be selected."))
        if (mod_input.device in LIST_DEVICES_ADC and
                (form_mod.adc_measurement.data == '' or
                 form_mod.adc_measurement_units.data == '')):
            error.append(gettext(
                "Both a measurement and unit must be selected."))
        if (mod_input.device != 'EDGE' and
                (mod_input.pre_output_duration and
                 form_mod.period.data < mod_input.pre_output_duration)):
            error.append(gettext(
                "The Read Period cannot be less than the Pre Output "
                "Duration"))
        if (form_mod.device_loc.data and
                not os.path.exists(form_mod.device_loc.data)):
            error.append(gettext(
                "Invalid device or improper permissions to read device"))

        if not error:
            mod_input.name = form_mod.name.data
            mod_input.i2c_bus = form_mod.i2c_bus.data
            if form_mod.location.data:
                mod_input.location = form_mod.location.data
            if form_mod.power_output_id.data:
                mod_input.power_output_id = form_mod.power_output_id.data
            else:
                mod_input.power_output_id = None
            if form_mod.baud_rate.data:
                mod_input.baud_rate = form_mod.baud_rate.data
            if form_mod.device_loc.data:
                mod_input.device_loc = form_mod.device_loc.data
            if form_mod.pre_output_id.data:
                mod_input.pre_output_id = form_mod.pre_output_id.data
            else:
                mod_input.pre_output_id = None

            if mod_input.device == 'LinuxCommand':
                mod_input.measurements = form_mod.cmd_measurement.data
                mod_input.convert_to_unit = '{meas},{unit}'.format(
                    meas=form_mod.cmd_measurement.data, unit=form_mod.cmd_measurement_units.data)

            short_list = []
            mod_units = False
            for key in request_form.keys():
                if 'convert_unit' in key:
                    mod_units = True
                    for value in request_form.getlist(key):
                        if value == 'default':
                            pass
                        elif (len(value.split(',')) < 2 or
                                value.split(',')[0] == '' or value.split(',')[1] == ''):
                            error.append("Invalid custom unit")
                        else:
                            short_list.append(value)
            if mod_units:
                mod_input.convert_to_unit = ';'.join(short_list)

            mod_input.pre_output_duration = form_mod.pre_output_duration.data
            mod_input.pre_output_during_measure = form_mod.pre_output_during_measure.data
            mod_input.period = form_mod.period.data
            mod_input.resolution = form_mod.resolution.data
            mod_input.resolution_2 = form_mod.resolution_2.data
            mod_input.sensitivity = form_mod.sensitivity.data
            mod_input.calibrate_sensor_measure = form_mod.calibrate_sensor_measure.data
            mod_input.cmd_command = form_mod.cmd_command.data
            mod_input.cmd_measurement = form_mod.cmd_measurement.data
            mod_input.cmd_measurement_units = form_mod.cmd_measurement_units.data
            mod_input.thermocouple_type = form_mod.thermocouple_type.data
            mod_input.ref_ohm = form_mod.ref_ohm.data
            # Serial options
            mod_input.pin_clock = form_mod.pin_clock.data
            mod_input.pin_cs = form_mod.pin_cs.data
            mod_input.pin_mosi = form_mod.pin_mosi.data
            mod_input.pin_miso = form_mod.pin_miso.data
            # Bluetooth options
            mod_input.bt_adapter = form_mod.bt_adapter.data
            # ADC options
            mod_input.adc_channel = form_mod.adc_channel.data
            mod_input.adc_gain = form_mod.adc_gain.data
            mod_input.adc_resolution = form_mod.adc_resolution.data
            mod_input.adc_measure = form_mod.adc_measurement.data
            mod_input.adc_measure_units = form_mod.adc_measurement_units.data
            mod_input.adc_volts_min = form_mod.adc_volts_min.data
            mod_input.adc_volts_max = form_mod.adc_volts_max.data
            mod_input.adc_units_min = form_mod.adc_units_min.data
            mod_input.adc_units_max = form_mod.adc_units_max.data
            mod_input.adc_inverse_unit_scale = form_mod.adc_inverse_unit_scale.data
            # Switch options
            mod_input.switch_edge = form_mod.switch_edge.data
            mod_input.switch_bouncetime = form_mod.switch_bounce_time.data
            mod_input.switch_reset_period = form_mod.switch_reset_period.data
            # PWM and RPM options
            mod_input.weighting = form_mod.weighting.data
            mod_input.rpm_pulses_per_rev = form_mod.rpm_pulses_per_rev.data
            mod_input.sample_time = form_mod.sample_time.data
            # Server options
            mod_input.port = form_mod.port.data
            mod_input.times_check = form_mod.times_check.data
            mod_input.deadline = form_mod.deadline.data
            # SHT sensor options
            if form_mod.sht_voltage.data:
                mod_input.sht_voltage = form_mod.sht_voltage.data
            db.session.commit()
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_data'))


def input_del(form_mod):
    action = '{action} {controller}'.format(
        action=gettext("Delete"),
        controller=gettext("Input"))
    error = []

    input_id = form_mod.input_id.data

    try:
        input_dev = Input.query.filter(
            Input.unique_id == input_id).first()
        if input_dev.is_activated:
            input_deactivate_associated_controllers(input_id)
            controller_activate_deactivate('deactivate', 'Input', input_id)

        delete_entry_with_id(Input, input_id)
        try:
            display_order = csv_to_list_of_str(
                DisplayOrder.query.first().inputs)
            display_order.remove(input_id)
            DisplayOrder.query.first().inputs = list_to_csv(display_order)
        except Exception:  # id not in list
            pass
        db.session.commit()
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_data'))


def input_reorder(input_id, display_order, direction):
    action = '{action} {controller}'.format(
        action=gettext("Reorder"),
        controller=gettext("Input"))
    error = []

    try:
        status, reord_list = reorder(display_order, input_id, direction)
        if status == 'success':
            DisplayOrder.query.first().inputs = ','.join(map(str, reord_list))
            db.session.commit()
        elif status == 'error':
            error.append(reord_list)
    except Exception as except_msg:
        error.append(except_msg)
    flash_success_errors(error, action, url_for('routes_page.page_data'))


def input_activate(form_mod):
    input_id = form_mod.input_id.data
    input_dev = Input.query.filter(Input.unique_id == input_id).first()
    if input_dev.device in LIST_DEVICES_SPI:
        if None in [form_mod.pin_clock.data,
                    form_mod.pin_cs.data,
                    form_mod.pin_miso.data]:
            flash("Cannot activate without Serial pins set.", "error")
            return redirect(url_for('routes_page.page_data'))
    elif (input_dev.device == 'LinuxCommand' and
          input_dev.cmd_command is ''):
        flash("Cannot activate Input without a command set.", "error")
        return redirect(url_for('routes_page.page_data'))
    elif (input_dev.device != 'LinuxCommand' and
            not input_dev.location and
            input_dev.device not in DEVICES_DEFAULT_LOCATION):
        flash("Cannot activate Input without the location (GPIO/I2C "
              "Address/Port/etc.) to communicate with it set.", "error")
        return redirect(url_for('routes_page.page_data'))
    controller_activate_deactivate('activate', 'Input',  input_id)


def input_deactivate(form_mod):
    input_id = form_mod.input_id.data
    input_deactivate_associated_controllers(input_id)
    controller_activate_deactivate('deactivate', 'Input', input_id)


# Deactivate any active PID or LCD controllers using this sensor
def input_deactivate_associated_controllers(input_id):
    # Deactivate any activated PIDs using this input
    sensor_unique_id = Input.query.filter(
        Input.unique_id == input_id).first().unique_id
    pid = PID.query.filter(PID.is_activated == True).all()
    for each_pid in pid:
        if sensor_unique_id in each_pid.measurement:
            controller_activate_deactivate('deactivate',
                                           'PID',
                                           each_pid.unique_id)
