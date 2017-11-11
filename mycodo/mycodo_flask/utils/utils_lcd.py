# -*- coding: utf-8 -*-
import logging
import sqlalchemy

from flask import flash
from flask import redirect
from flask import url_for

from mycodo.mycodo_flask.extensions import db
from flask_babel import gettext
from RPi import GPIO

from mycodo.mycodo_client import DaemonControl

from mycodo.databases.models import DisplayOrder
from mycodo.databases.models import LCD
from mycodo.databases.models import Sensor
from mycodo.utils.system_pi import csv_to_list_of_int
from mycodo.utils.system_pi import list_to_csv

from mycodo.mycodo_flask.utils.utils_general import add_display_order
from mycodo.mycodo_flask.utils.utils_general import controller_activate_deactivate
from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.mycodo_flask.utils.utils_general import flash_form_errors
from mycodo.mycodo_flask.utils.utils_general import flash_success_errors
from mycodo.mycodo_flask.utils.utils_general import reorder

logger = logging.getLogger(__name__)


#
# LCD Manipulation
#

def lcd_add(quantity):
    action = u'{action} {controller}'.format(
        action=gettext(u"Add"),
        controller=gettext(u"LCD"))
    error = []
    for _ in range(0, quantity):
        try:
            new_lcd = LCD()
            if GPIO.RPI_REVISION == 2 or GPIO.RPI_REVISION == 3:
                new_lcd.i2c_bus = 1
            else:
                new_lcd.i2c_bus = 0
            new_lcd.save()
            display_order = csv_to_list_of_int(DisplayOrder.query.first().lcd)
            DisplayOrder.query.first().lcd = add_display_order(
                display_order, new_lcd.id)
            db.session.commit()
        except sqlalchemy.exc.OperationalError as except_msg:
            error.append(except_msg)
        except sqlalchemy.exc.IntegrityError as except_msg:
            error.append(except_msg)
        flash_success_errors(error, action, url_for('page_routes.page_lcd'))


def lcd_mod(form_mod_lcd):
    action = u'{action} {controller}'.format(
        action=gettext(u"Modify"),
        controller=gettext(u"LCD"))
    error = []

    if form_mod_lcd.validate():
        try:
            mod_lcd = LCD.query.filter(
                LCD.id == form_mod_lcd.lcd_id.data).first()
            if mod_lcd.is_activated:
                flash(gettext(u"Deactivate LCD controller before modifying"
                              u" its settings."), "error")
                return redirect('/lcd')
            mod_lcd = LCD.query.filter(
                LCD.id == form_mod_lcd.lcd_id.data).first()
            mod_lcd.name = form_mod_lcd.name.data
            mod_lcd.location = form_mod_lcd.location.data
            mod_lcd.i2c_bus = form_mod_lcd.i2c_bus.data
            mod_lcd.multiplexer_address = form_mod_lcd.multiplexer_address.data
            mod_lcd.multiplexer_channel = form_mod_lcd.multiplexer_channel.data
            mod_lcd.period = form_mod_lcd.period.data
            mod_lcd.x_characters = int(form_mod_lcd.lcd_type.data.split("x")[0])
            mod_lcd.y_lines = int(form_mod_lcd.lcd_type.data.split("x")[1])
            if form_mod_lcd.line_1_display.data:
                mod_lcd.line_1_sensor_id = form_mod_lcd.line_1_display.data.split(",")[0]
                mod_lcd.line_1_measurement = form_mod_lcd.line_1_display.data.split(",")[1]
            else:
                mod_lcd.line_1_sensor_id = ''
                mod_lcd.line_1_measurement = ''
            if form_mod_lcd.line_2_display.data:
                mod_lcd.line_2_sensor_id = form_mod_lcd.line_2_display.data.split(",")[0]
                mod_lcd.line_2_measurement = form_mod_lcd.line_2_display.data.split(",")[1]
            else:
                mod_lcd.line_2_sensor_id = ''
                mod_lcd.line_2_measurement = ''
            if form_mod_lcd.line_3_display.data:
                mod_lcd.line_3_sensor_id = form_mod_lcd.line_3_display.data.split(",")[0]
                mod_lcd.line_3_measurement = form_mod_lcd.line_3_display.data.split(",")[1]
            else:
                mod_lcd.line_3_sensor_id = ''
                mod_lcd.line_3_measurement = ''
            if form_mod_lcd.line_4_display.data:
                mod_lcd.line_4_sensor_id = form_mod_lcd.line_4_display.data.split(",")[0]
                mod_lcd.line_4_measurement = form_mod_lcd.line_4_display.data.split(",")[1]
            else:
                mod_lcd.line_4_sensor_id = ''
                mod_lcd.line_4_measurement = ''
            db.session.commit()
        except Exception as except_msg:
            error.append(except_msg)
        flash_success_errors(error, action, url_for('page_routes.page_lcd'))
    else:
        flash_form_errors(form_mod_lcd)


def lcd_del(lcd_id):
    action = u'{action} {controller}'.format(
        action=gettext(u"Delete"),
        controller=gettext(u"LCD"))
    error = []

    try:
        delete_entry_with_id(LCD,
                             lcd_id)
        display_order = csv_to_list_of_int(DisplayOrder.query.first().lcd)
        display_order.remove(int(lcd_id))
        DisplayOrder.query.first().lcd = list_to_csv(display_order)
        db.session.commit()
    except Exception as except_msg:
        error.append(except_msg)
    flash_success_errors(error, action, url_for('page_routes.page_lcd'))


def lcd_reorder(lcd_id, display_order, direction):
    action = u'{action} {controller}'.format(
        action=gettext(u"Reorder"),
        controller=gettext(u"LCD"))
    error = []
    try:
        status, reord_list = reorder(display_order,
                                     lcd_id,
                                     direction)
        if status == 'success':
            DisplayOrder.query.first().lcd = ','.join(map(str, reord_list))
            db.session.commit()
        else:
            error.append(reord_list)
    except Exception as except_msg:
        error.append(except_msg)
    flash_success_errors(error, action, url_for('page_routes.page_lcd'))


def lcd_activate(lcd_id):
    action = u'{action} {controller}'.format(
        action=gettext(u"Activate"),
        controller=gettext(u"LCD"))
    error = []

    try:
        # All sensors the LCD depends on must be active to activate the LCD
        lcd = LCD.query.filter(
            LCD.id == lcd_id).first()
        if lcd.y_lines == 2:
            lcd_lines = [lcd.line_1_sensor_id,
                         lcd.line_2_sensor_id]
        else:
            lcd_lines = [lcd.line_1_sensor_id,
                         lcd.line_2_sensor_id,
                         lcd.line_3_sensor_id,
                         lcd.line_4_sensor_id]
        # Filter only sensors that will be displayed
        sensor = Sensor.query.filter(
            Sensor.id.in_(lcd_lines)).all()
        # Check if any sensors are not active
        for each_sensor in sensor:
            if not each_sensor.is_activated:
                flash(gettext(
                    u"Cannot activate controller if the associated "
                    u"sensor controller is inactive"), "error")
                return redirect('/lcd')
        controller_activate_deactivate(
            'activate',
            'LCD',
            lcd_id)
    except Exception as except_msg:
        error.append(except_msg)
    flash_success_errors(error, action, url_for('page_routes.page_lcd'))


def lcd_deactivate(lcd_id):
    controller_activate_deactivate(
        'deactivate',
        'LCD',
        lcd_id)


def lcd_reset_flashing(lcd_id):
    control = DaemonControl()
    return_value, return_msg = control.flash_lcd(
        lcd_id, 0)
    if return_value:
        flash(gettext(u"%(msg)s", msg=return_msg), "success")
    else:
        flash(gettext(u"%(msg)s", msg=return_msg), "error")
