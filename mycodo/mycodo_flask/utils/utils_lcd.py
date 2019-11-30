# -*- coding: utf-8 -*-
import logging

import sqlalchemy
from flask import current_app
from flask import flash
from flask import redirect
from flask import url_for
from flask_babel import gettext

from mycodo.config import LCD_INFO
from mycodo.config_translations import TRANSLATIONS
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
from mycodo.mycodo_flask.utils.utils_general import return_dependencies
from mycodo.utils.system_pi import csv_to_list_of_str
from mycodo.utils.system_pi import list_to_csv

logger = logging.getLogger(__name__)


#
# LCD Manipulation
#

def lcd_add(form):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['add']['title'],
        controller=TRANSLATIONS['lcd']['title'])
    error = []

    if current_app.config['TESTING']:
        dep_unmet = False
    else:
        dep_unmet, _ = return_dependencies(form.lcd_type.data)
        if dep_unmet:
            list_unmet_deps = []
            for each_dep in dep_unmet:
                list_unmet_deps.append(each_dep[0])
            error.append("The {dev} device you're trying to add has unmet dependencies: {dep}".format(
                dev=form.lcd_type.data, dep=', '.join(list_unmet_deps)))

    try:
        new_lcd = LCD()
        new_lcd_data = LCDData()

        try:
            from RPi import GPIO
            if GPIO.RPI_REVISION == 2 or GPIO.RPI_REVISION == 3:
                new_lcd.i2c_bus = 1
            else:
                new_lcd.i2c_bus = 0
        except:
            logger.error(
                "RPi.GPIO and Raspberry Pi required for this action")

        new_lcd.lcd_type = form.lcd_type.data
        new_lcd.name = str(LCD_INFO[form.lcd_type.data]['name'])

        if form.lcd_type.data == '128x32_pioled':
            new_lcd.location = '0x3c'
            new_lcd.x_characters = 21
            new_lcd.y_lines = 4
        elif form.lcd_type.data == '128x64_pioled':
            new_lcd.location = '0x3c'
            new_lcd.x_characters = 21
            new_lcd.y_lines = 8
        elif form.lcd_type.data == '16x2_generic':
            new_lcd.location = '0x27'
            new_lcd.x_characters = 16
            new_lcd.y_lines = 2
        elif form.lcd_type.data == '20x4_generic':
            new_lcd.location = '0x27'
            new_lcd.x_characters = 20
            new_lcd.y_lines = 4

        if not error:
            new_lcd.save()
            new_lcd_data.lcd_id = new_lcd.unique_id
            new_lcd_data.save()
            display_order = csv_to_list_of_str(DisplayOrder.query.first().lcd)
            DisplayOrder.query.first().lcd = add_display_order(
                display_order, new_lcd.unique_id)
            db.session.commit()
    except sqlalchemy.exc.OperationalError as except_msg:
        error.append(except_msg)
    except sqlalchemy.exc.IntegrityError as except_msg:
        error.append(except_msg)
    flash_success_errors(error, action, url_for('routes_page.page_lcd'))

    if dep_unmet:
        return 1


def lcd_mod(form_mod_lcd):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['modify']['title'],
        controller=TRANSLATIONS['lcd']['title'])
    error = []

    mod_lcd = LCD.query.filter(
        LCD.unique_id == form_mod_lcd.lcd_id.data).first()
    if mod_lcd.is_activated:
        error.append(gettext("Deactivate LCD controller before modifying"
                             " its settings."))

    if not error:
        if form_mod_lcd.validate():
            try:
                mod_lcd.name = form_mod_lcd.name.data
                mod_lcd.location = form_mod_lcd.location.data
                mod_lcd.i2c_bus = form_mod_lcd.i2c_bus.data
                if form_mod_lcd.pin_reset.data is not None:
                    mod_lcd.pin_reset = form_mod_lcd.pin_reset.data
                else:
                    mod_lcd.pin_reset = None
                mod_lcd.period = form_mod_lcd.period.data
                mod_lcd.log_level_debug = form_mod_lcd.log_level_debug.data
                db.session.commit()
            except Exception as except_msg:
                error.append(except_msg)
        else:
            flash_form_errors(form_mod_lcd)
    flash_success_errors(error, action, url_for('routes_page.page_lcd'))


def lcd_del(lcd_id):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['delete']['title'],
        controller=TRANSLATIONS['lcd']['title'])
    error = []

    lcd = LCD.query.filter(
        LCD.unique_id == lcd_id).first()
    if lcd.is_activated:
        error.append(gettext("Deactivate LCD controller before modifying "
                             "its settings."))

    if not error:
        try:
            # Delete all LCD Displays
            lcd_displays = LCDData.query.filter(
                LCDData.lcd_id == lcd_id).all()
            for each_lcd_display in lcd_displays:
                lcd_display_del(each_lcd_display.unique_id, delete_last=True)

            # Delete LCD
            delete_entry_with_id(LCD, lcd_id)
            display_order = csv_to_list_of_str(DisplayOrder.query.first().lcd)
            display_order.remove(lcd_id)
            DisplayOrder.query.first().lcd = list_to_csv(display_order)
            db.session.commit()
        except Exception as except_msg:
            error.append(except_msg)
    flash_success_errors(error, action, url_for('routes_page.page_lcd'))


def lcd_reorder(lcd_id, display_order, direction):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['reorder']['title'],
        controller=TRANSLATIONS['lcd']['title'])
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
    flash_success_errors(error, action, url_for('routes_page.page_lcd'))


def lcd_activate(lcd_id):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['activate']['title'],
        controller=TRANSLATIONS['lcd']['title'])
    error = []

    try:
        # All display lines must be filled to activate display
        lcd = LCD.query.filter(
            LCD.unique_id == lcd_id).first()
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
                "Cannot activate LCD if there are blank lines"))

        if not error:
            controller_activate_deactivate('activate', 'LCD', lcd_id)
    except Exception as except_msg:
        error.append(except_msg)
    flash_success_errors(error, action, url_for('routes_page.page_lcd'))


def lcd_deactivate(lcd_id):
    controller_activate_deactivate('deactivate', 'LCD', lcd_id)


def lcd_reset_flashing(lcd_id):
    control = DaemonControl()
    return_value, return_msg = control.lcd_flash(lcd_id, False)
    if return_value:
        flash(gettext("%(msg)s", msg=return_msg), "success")
    else:
        flash(gettext("%(msg)s", msg=return_msg), "error")


def lcd_display_add(form):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['add']['title'],
        controller=TRANSLATIONS['display']['title'])
    error = []

    lcd = LCD.query.filter(
        LCD.unique_id == form.lcd_id.data).first()
    if lcd.is_activated:
        error.append(gettext("Deactivate LCD controller before modifying"
                             " its settings."))

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
    flash_success_errors(error, action, url_for('routes_page.page_lcd'))


def lcd_display_mod(form):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['modify']['title'],
        controller=TRANSLATIONS['display']['title'])
    error = []

    lcd = LCD.query.filter(
        LCD.unique_id == form.lcd_id.data).first()
    if lcd.is_activated:
        error.append(gettext("Deactivate LCD controller before modifying"
                             " its settings."))

    if not error:
        try:
            mod_lcd = LCD.query.filter(
                LCD.unique_id == form.lcd_id.data).first()
            if mod_lcd.is_activated:
                flash(gettext("Deactivate LCD controller before modifying"
                              " its settings."), "error")
                return redirect('/lcd')

            mod_lcd_data = LCDData.query.filter(
                LCDData.unique_id == form.lcd_data_id.data).first()

            if form.line_1_display.data:
                mod_lcd_data.line_1_id = form.line_1_display.data.split(",")[0]
                mod_lcd_data.line_1_measurement = form.line_1_display.data.split(",")[1]
                if form.line_1_text.data:
                    mod_lcd_data.line_1_text = form.line_1_text.data
                mod_lcd_data.line_1_max_age = form.line_1_max_age.data
                mod_lcd_data.line_1_decimal_places = form.line_1_decimal_places.data
            else:
                mod_lcd_data.line_1_id = ''
                mod_lcd_data.line_1_measurement = ''

            if form.line_2_display.data:
                mod_lcd_data.line_2_id = form.line_2_display.data.split(",")[0]
                mod_lcd_data.line_2_measurement = form.line_2_display.data.split(",")[1]
                if form.line_2_text.data:
                    mod_lcd_data.line_2_text = form.line_2_text.data
                mod_lcd_data.line_2_max_age = form.line_2_max_age.data
                mod_lcd_data.line_2_decimal_places = form.line_2_decimal_places.data
            else:
                mod_lcd_data.line_2_id = ''
                mod_lcd_data.line_2_measurement = ''

            if form.line_3_display.data:
                mod_lcd_data.line_3_id = form.line_3_display.data.split(",")[0]
                mod_lcd_data.line_3_measurement = form.line_3_display.data.split(",")[1]
                if form.line_3_text.data:
                    mod_lcd_data.line_3_text = form.line_3_text.data
                mod_lcd_data.line_3_max_age = form.line_3_max_age.data
                mod_lcd_data.line_3_decimal_places = form.line_3_decimal_places.data
            else:
                mod_lcd_data.line_3_id = ''
                mod_lcd_data.line_3_measurement = ''

            if form.line_4_display.data:
                mod_lcd_data.line_4_id = form.line_4_display.data.split(",")[0]
                mod_lcd_data.line_4_measurement = form.line_4_display.data.split(",")[1]
                if form.line_4_text.data:
                    mod_lcd_data.line_4_text = form.line_4_text.data
                mod_lcd_data.line_4_max_age = form.line_4_max_age.data
                mod_lcd_data.line_4_decimal_places = form.line_4_decimal_places.data
            else:
                mod_lcd_data.line_4_id = ''
                mod_lcd_data.line_4_measurement = ''

            if form.line_5_display.data:
                mod_lcd_data.line_5_id = form.line_5_display.data.split(",")[0]
                mod_lcd_data.line_5_measurement = form.line_5_display.data.split(",")[1]
                if form.line_5_text.data:
                    mod_lcd_data.line_5_text = form.line_5_text.data
                mod_lcd_data.line_5_max_age = form.line_5_max_age.data
                mod_lcd_data.line_5_decimal_places = form.line_5_decimal_places.data
            else:
                mod_lcd_data.line_5_id = ''
                mod_lcd_data.line_5_measurement = ''

            if form.line_6_display.data:
                mod_lcd_data.line_6_id = form.line_6_display.data.split(",")[0]
                mod_lcd_data.line_6_measurement = form.line_6_display.data.split(",")[1]
                if form.line_6_text.data:
                    mod_lcd_data.line_6_text = form.line_6_text.data
                mod_lcd_data.line_6_max_age = form.line_6_max_age.data
                mod_lcd_data.line_6_decimal_places = form.line_6_decimal_places.data
            else:
                mod_lcd_data.line_6_id = ''
                mod_lcd_data.line_6_measurement = ''

            if form.line_7_display.data:
                mod_lcd_data.line_7_id = form.line_7_display.data.split(",")[0]
                mod_lcd_data.line_7_measurement = form.line_7_display.data.split(",")[1]
                if form.line_7_text.data:
                    mod_lcd_data.line_7_text = form.line_7_text.data
                mod_lcd_data.line_7_max_age = form.line_7_max_age.data
                mod_lcd_data.line_7_decimal_places = form.line_7_decimal_places.data
            else:
                mod_lcd_data.line_7_id = ''
                mod_lcd_data.line_7_measurement = ''

            if form.line_8_display.data:
                mod_lcd_data.line_8_id = form.line_8_display.data.split(",")[0]
                mod_lcd_data.line_8_measurement = form.line_8_display.data.split(",")[1]
                if form.line_8_text.data:
                    mod_lcd_data.line_8_text = form.line_8_text.data
                mod_lcd_data.line_8_max_age = form.line_8_max_age.data
                mod_lcd_data.line_8_decimal_places = form.line_8_decimal_places.data
            else:
                mod_lcd_data.line_8_id = ''
                mod_lcd_data.line_8_measurement = ''

            db.session.commit()
        except Exception as except_msg:
            error.append(except_msg)
    flash_success_errors(error, action, url_for('routes_page.page_lcd'))


def lcd_display_del(lcd_data_id, delete_last=False):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['delete']['title'],
        controller=TRANSLATIONS['display']['title'])
    error = []

    lcd_data_this = LCDData.query.filter(
        LCDData.unique_id == lcd_data_id).first()
    lcd_data_all = LCDData.query.filter(
        LCDData.lcd_id == lcd_data_this.lcd_id).all()
    lcd = LCD.query.filter(
        LCD.unique_id == lcd_data_this.lcd_id).first()

    if lcd.is_activated:
        error.append(gettext("Deactivate LCD controller before modifying"
                             " its settings"))
    if not delete_last and len(lcd_data_all) < 2:
        error.append(gettext("The last display cannot be deleted"))

    if not error:
        try:
            delete_entry_with_id(LCDData,
                                 lcd_data_id)
            db.session.commit()
        except Exception as except_msg:
            error.append(except_msg)
    flash_success_errors(error, action, url_for('routes_page.page_lcd'))
