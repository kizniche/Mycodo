# -*- coding: utf-8 -*-
import logging
import textwrap

from mycodo.config import PATH_PYTHON_CODE_USER
from mycodo.utils.system_pi import assure_path_exists
from mycodo.utils.system_pi import cmd_output
from mycodo.utils.system_pi import set_user_grp

logger = logging.getLogger(__name__)


pre_statement_run = """import os
import sys
sys.path.append(os.path.abspath('/var/mycodo-root'))
from mycodo.controllers.base_conditional import AbstractConditional
from mycodo.mycodo_client import DaemonControl
control = DaemonControl()

class ConditionalRun(AbstractConditional):
    def __init__(self, logger, function_id, message):
        super(ConditionalRun, self).__init__(logger, function_id, message)

        self.logger = logger
        self.function_id = function_id
        self.variables = {}
        self.message = message
        self.running = True

    def conditional_code_run(self):
"""


def cond_statement_replace(
        cond_statement,
        table_conditions_all,
        table_actions_all):
    """Replace short condition/action IDs in conditional statement with full condition/action IDs"""
    cond_statement_replaced = cond_statement
    for each_condition in table_conditions_all:
        condition_id_short = each_condition.unique_id.split('-')[0]
        cond_statement_replaced = cond_statement_replaced.replace(
            '{{{id}}}'.format(id=condition_id_short),
            each_condition.unique_id)

    for each_action in table_actions_all:
        action_id_short = each_action.unique_id.split('-')[0]
        cond_statement_replaced = cond_statement_replaced.replace(
            '{{{id}}}'.format(id=action_id_short),
            each_action.unique_id)

    return cond_statement_replaced


def save_conditional_code(
        error,
        cond_statement,
        unique_id,
        table_conditions_all,
        table_actions_all,
        test=False):
    lines_code = None
    cmd_status = None
    cmd_out = None

    try:
        indented_code = textwrap.indent(cond_statement, ' ' * 8)

        cond_statement_run = pre_statement_run + indented_code
        cond_statement_run = cond_statement_replace(
            cond_statement_run, table_conditions_all, table_actions_all)

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

            cmd_test = 'mkdir -p /var/mycodo-root/.pylint.d && ' \
                       'export PYTHONPATH=$PYTHONPATH:/var/mycodo-root && ' \
                       'export PYLINTHOME=/var/mycodo-root/.pylint.d && ' \
                       'pylint3 -d I,W0621,C0103,C0111,C0301,C0327,C0410,C0413,R0912,R0914,R0915 {path}'.format(
                           path=file_run)
            cmd_out, _, cmd_status = cmd_output(cmd_test)
    except Exception as err:
        error.append("Error saving/testing conditional code: {}".format(err))

    return error, lines_code, cmd_status, cmd_out
