# -*- coding: utf-8 -*-
import logging

import sqlalchemy
from RPi import GPIO
from flask import flash
from flask import redirect
from flask import url_for
from flask_babel import gettext

from mycodo.databases.models import DisplayOrder
from mycodo.databases.models import LCD
from mycodo.databases.models import LCDData
from mycodo.mycodo_client import DaemonControl
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.utils.utils_general import add_display_order
from mycodo.mycodo_flask.utils.utils_general import controller_activate_deactivate
from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.mycodo_flask.utils.utils_general import flash_form_errors
from mycodo.mycodo_flask.utils.utils_general import flash_success_errors
from mycodo.mycodo_flask.utils.utils_general import reorder
from mycodo.utils.system_pi import csv_to_list_of_int
from mycodo.utils.system_pi import list_to_csv

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
            new_lcd_data = LCDData()
            if GPIO.RPI_REVISION == 2 or GPIO.RPI_REVISION == 3:
                new_lcd.i2c_bus = 1
            else:
                new_lcd.i2c_bus = 0
            new_lcd.save()
            new_lcd_data.lcd_id = new_lcd.id
            new_lcd_data.save()
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

    lcd = LCD.query.filter(
        LCD.id == form_mod_lcd.lcd_id.data).first()
    if lcd.is_activated:
        error.append(gettext(u"Deactivate LCD controller before modifying"
                             u" its settings."))

    if not error:
        if form_mod_lcd.validate():
            try:
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
                db.session.commit()
            except Exception as except_msg:
                error.append(except_msg)
        else:
            flash_form_errors(form_mod_lcd)
    flash_success_errors(error, action, url_for('page_routes.page_lcd'))


def lcd_del(lcd_id):
    action = u'{action} {controller}'.format(
        action=gettext(u"Delete"),
        controller=gettext(u"LCD"))
    error = []

    lcd = LCD.query.filter(
        LCD.id == lcd_id).first()
    if lcd.is_activated:
        error.append(gettext(u"Deactivate LCD controller before modifying "
                             u"its settings."))

    if not error:
        try:
            # Delete all LCD Displays
            lcd_displays = LCDData.query.filter(
                LCDData.lcd_id == lcd_id).all()
            for each_lcd_display in lcd_displays:
                lcd_display_del(each_lcd_display.id, delete_last=True)

            # Delete LCD
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
        # All display lines must be filled to activate display
        lcd = LCD.query.filter(
            LCD.id == lcd_id).first()
        lcd_data = LCDData.query.filter(
            LCDData.lcd_id == lcd_id).all()
        blank_line_detected = False

        for each_lcd_data in lcd_data:
            if (
                    (lcd.y_lines in [2, 4] and
                        (not each_lcd_data.line_1_id or
                         not each_lcd_data.line_2_id)
                     ) or
                    (lcd.y_lines == 4 and
                        (not each_lcd_data.line_3_id or
                         not each_lcd_data.line_4_id))
                    ):
                blank_line_detected = True

        if blank_line_detected:
            error.append(gettext(
                u"Cannot activate LCD if there are blank lines"))

        if not error:
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


def lcd_display_add(form):
    action = u'{action} {controller}'.format(
        action=gettext(u"Add"),
        controller=gettext(u"Display"))
    error = []

    lcd = LCD.query.filter(
        LCD.id == form.lcd_id.data).first()
    if lcd.is_activated:
        error.append(gettext(u"Deactivate LCD controller before modifying"
                             u" its settings."))

    if not error:
        try:
            new_lcd_data = LCDData()
            new_lcd_data.lcd_id = form.lcd_id.data
            new_lcd_data.save()
            db.session.commit()
        except sqlalchemy.exc.OperationalError as except_msg:
            error.append(except_msg)
        except sqlalchemy.exc.IntegrityError as except_msg:
            error.append(except_msg)
    flash_success_errors(error, action, url_for('page_routes.page_lcd'))


def lcd_display_mod(form):
    action = u'{action} {controller}'.format(
        action=gettext(u"Mod"),
        controller=gettext(u"Display"))
    error = []

    lcd = LCD.query.filter(
        LCD.id == form.lcd_id.data).first()
    if lcd.is_activated:
        error.append(gettext(u"Deactivate LCD controller before modifying"
                             u" its settings."))

    if not error:
        try:
            mod_lcd = LCD.query.filter(
                LCD.id == form.lcd_id.data).first()
            if mod_lcd.is_activated:
                flash(gettext(u"Deactivate LCD controller before modifying"
                              u" its settings."), "error")
                return redirect('/lcd')

            mod_lcd_data = LCDData.query.filter(
                LCDData.id == form.lcd_data_id.data).first()

            if form.line_1_display.data:
                mod_lcd_data.line_1_id = form.line_1_display.data.split(",")[0]
                mod_lcd_data.line_1_measurement = form.line_1_display.data.split(",")[1]
                mod_lcd_data.line_1_max_age = form.line_1_max_age.data
                mod_lcd_data.line_1_decimal_places = form.line_1_decimal_places.data
            else:
                mod_lcd_data.line_1_id = ''
                mod_lcd_data.line_1_measurement = ''

            if form.line_2_display.data:
                mod_lcd_data.line_2_id = form.line_2_display.data.split(",")[0]
                mod_lcd_data.line_2_measurement = form.line_2_display.data.split(",")[1]
                mod_lcd_data.line_2_max_age = form.line_2_max_age.data
                mod_lcd_data.line_2_decimal_places = form.line_2_decimal_places.data
            else:
                mod_lcd_data.line_2_id = ''
                mod_lcd_data.line_2_measurement = ''

            if form.line_3_display.data:
                mod_lcd_data.line_3_id = form.line_3_display.data.split(",")[0]
                mod_lcd_data.line_3_measurement = form.line_3_display.data.split(",")[1]
                mod_lcd_data.line_3_max_age = form.line_3_max_age.data
                mod_lcd_data.line_3_decimal_places = form.line_3_decimal_places.data
            else:
                mod_lcd_data.line_3_id = ''
                mod_lcd_data.line_3_measurement = ''

            if form.line_4_display.data:
                mod_lcd_data.line_4_id = form.line_4_display.data.split(",")[0]
                mod_lcd_data.line_4_measurement = form.line_4_display.data.split(",")[1]
                mod_lcd_data.line_4_max_age = form.line_4_max_age.data
                mod_lcd_data.line_4_decimal_places = form.line_4_decimal_places.data
            else:
                mod_lcd_data.line_4_id = ''
                mod_lcd_data.line_4_measurement = ''

            db.session.commit()
        except Exception as except_msg:
            error.append(except_msg)
    flash_success_errors(error, action, url_for('page_routes.page_lcd'))


def lcd_display_del(lcd_data_id, delete_last=False):
    action = u'{action} {controller}'.format(
        action=gettext(u"Delete"),
        controller=gettext(u"Display"))
    error = []

    lcd_data_this = LCDData.query.filter(
        LCDData.id == lcd_data_id).first()
    lcd_data_all = LCDData.query.filter(
        LCDData.lcd_id == lcd_data_this.lcd_id).all()
    lcd = LCD.query.filter(
        LCD.id == lcd_data_this.lcd_id).first()

    if lcd.is_activated:
        error.append(gettext(u"Deactivate LCD controller before modifying"
                             u" its settings"))
    if not delete_last and len(lcd_data_all) < 2:
        error.append(gettext(u"The last display cannot be deleted"))

    if not error:
        try:
            delete_entry_with_id(LCDData,
                                 lcd_data_id)
            db.session.commit()
        except Exception as except_msg:
            error.append(except_msg)
    flash_success_errors(error, action, url_for('page_routes.page_lcd'))
