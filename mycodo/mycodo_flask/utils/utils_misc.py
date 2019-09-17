# -*- coding: utf-8 -*-
import logging
import textwrap

import sqlalchemy
from flask import Markup
from flask import flash
from flask import url_for
from flask_babel import gettext

from mycodo.config import PATH_PYTHON_CODE_USER
from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import Actions
from mycodo.databases.models import ConditionalConditions
from mycodo.databases.models import EnergyUsage
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.mycodo_flask.utils.utils_general import flash_success_errors
from mycodo.utils.system_pi import assure_path_exists
from mycodo.utils.system_pi import cmd_output
from mycodo.utils.system_pi import set_user_grp

logger = logging.getLogger(__name__)


#
# Conditional
#

pre_statement_run = """import os
import sys
sys.path.append(os.path.abspath('/var/mycodo-root'))
from mycodo.mycodo_client import DaemonControl
control = DaemonControl()

class ConditionalRun:
    def __init__(self, logger, function_id, message):
        self.logger = logger
        self.function_id = function_id
        self.message = message

    def run_all_actions(self, message=None):
        if message is None:
            message = self.message
        control.trigger_all_actions(self.function_id, message=message)

    def run_action(self, action_id, message=None):
        if message is None:
            message = self.message
        control.trigger_action(action_id, message=message, single_action=True)

    def measure(self, condition_id):
        return control.get_condition_measurement(condition_id, function_id=self.function_id)

    @staticmethod
    def measure_dict(condition_id):
        string_sets = control.get_condition_measurement_dict(condition_id)
        if string_sets:
            list_ts_values = []
            for each_set in string_sets.split(';'):
                ts_value = each_set.split(',')
                list_ts_values.append({{'time': ts_value[0], 'value': float(ts_value[1])}})
            return list_ts_values
        return None

    def conditional_code_run(self):
"""

def cond_statement_replace(cond_statement):
    """Replace short condition/action IDs in conditional statement with full condition/action IDs"""
    cond_statement_replaced = cond_statement
    for each_condition in ConditionalConditions.query.all():
        condition_id_short = each_condition.unique_id.split('-')[0]
        cond_statement_replaced = cond_statement_replaced.replace(
            '{{{id}}}'.format(id=condition_id_short),
            each_condition.unique_id)

    for each_action in Actions.query.all():
        action_id_short = each_action.unique_id.split('-')[0]
        cond_statement_replaced = cond_statement_replaced.replace(
            '{{{id}}}'.format(id=action_id_short),
            each_action.unique_id)

    return cond_statement_replaced

def save_conditional_code(error, cond_statement, unique_id, test=False):
    indented_code = textwrap.indent(
        cond_statement, ' ' * 8)

    cond_statement_run = pre_statement_run + indented_code
    cond_statement_run = cond_statement_replace(cond_statement_run)

    assure_path_exists(PATH_PYTHON_CODE_USER)
    file_run = '{}/conditional_{}.py'.format(
        PATH_PYTHON_CODE_USER, unique_id)
    with open(file_run, 'w') as fw:
        fw.write('{}\n'.format(cond_statement_run))
        fw.close()
    set_user_grp(file_run, 'mycodo', 'mycodo')

    if len(cond_statement_run.splitlines()) > 999:
        error.append("Too many lines in code. Reduce code to less than 1000 lines.")

    if test:
        lines_code = ''
        for line_num, each_line in enumerate(cond_statement_run.splitlines(), 1):
            if len(str(line_num)) == 3:
                line_spacing = ''
            elif len(str(line_num)) == 2:
                line_spacing = ' '
            else:
                line_spacing = '  '
            lines_code += '{sp}{ln}: {line}\n'.format(
                sp=line_spacing,
                ln=line_num,
                line=each_line)

        cmd_test = 'export PYTHONPATH=$PYTHONPATH:/var/mycodo-root && ' \
                   'pylint3 -d I,W0621,C0103,C0111,C0301,C0327,C0410,C0413 {path}'.format(
            path=file_run)
        cmd_out, _, cmd_status = cmd_output(cmd_test)

        message = Markup(
            '<pre>\n\n'
            'Full Conditional Statement code:\n\n{code}\n\n'
            'Conditional Statement code analysis:\n\n{report}'
            '</pre>'.format(
                code=lines_code, report=cmd_out.decode("utf-8")))
        if cmd_status:
            flash('Error(s) were found while evaluating your code. Review '
                  'the error(s), below, and fix them before activating your '
                  'Conditional.', 'error')
            flash(message, 'error')
        else:
            flash(
                "No errors were found while evaluating your code. However, "
                "this doesn't mean your code will perform as expected. "
                "Review your code for issues and test your Conditional "
                "before putting it into a production environment.", 'success')
            flash(message, 'success')

    return error


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
