# -*- coding: utf-8 -*-
import logging

import sqlalchemy
from flask import flash
from flask import url_for
from flask_babel import gettext

from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import EnergyUsage
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.mycodo_flask.utils.utils_general import flash_success_errors

logger = logging.getLogger(__name__)


#
# Math manipulation
#

def energy_usage_add(form_add_energy_usage):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['add']['title'],
        controller=TRANSLATIONS['energy_usage']['title'])
    error = []

    new_energy_usage = EnergyUsage()
    new_energy_usage.device_id = form_add_energy_usage.energy_usage_select.data.split(',')[0]
    new_energy_usage.measurement_id = form_add_energy_usage.energy_usage_select.data.split(',')[1]

    if not error:
        try:
            new_energy_usage.save()

            flash(gettext(
                "Energy Usage with ID %(id)s (%(uuid)s) successfully added",
                id=new_energy_usage.id,
                uuid=new_energy_usage.unique_id),
                  "success")
        except sqlalchemy.exc.OperationalError as except_msg:
            error.append(except_msg)
        except sqlalchemy.exc.IntegrityError as except_msg:
            error.append(except_msg)
    flash_success_errors(error, action, url_for('routes_page.page_data'))


def energy_usage_mod(form_mod_energy_usage):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['modify']['title'],
        controller=TRANSLATIONS['energy_usage']['title'])
    error = []

    try:
        mod_energy_usage = EnergyUsage.query.filter(
            EnergyUsage.unique_id == form_mod_energy_usage.energy_usage_id.data).first()

        mod_energy_usage.name = form_mod_energy_usage.name.data
        mod_energy_usage.device_id = form_mod_energy_usage.selection_device_measure_ids.data.split(',')[0]
        mod_energy_usage.measurement_id = form_mod_energy_usage.selection_device_measure_ids.data.split(',')[1]

        if not error:
            db.session.commit()
    except Exception as except_msg:
        logger.exception(1)
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_data'))


def energy_usage_delete(energy_usage_id):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['delete']['title'],
        controller=TRANSLATIONS['energy_usage']['title'])
    error = []

    try:
        delete_entry_with_id(EnergyUsage, energy_usage_id)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_data'))
