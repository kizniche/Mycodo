# -*- coding: utf-8 -*-
import logging

import os
from flask import Markup

from mycodo.config import PATH_PYTHON_CODE_USER
from mycodo.utils.system_pi import assure_path_exists
from mycodo.utils.system_pi import cmd_output
from mycodo.utils.system_pi import set_user_grp

logger = logging.getLogger(__name__)


def create_python_file(python_code_run, filename):
    assure_path_exists(PATH_PYTHON_CODE_USER)
    file_run = os.path.join(PATH_PYTHON_CODE_USER, filename)
    with open(file_run, 'w') as fw:
        fw.write('{}\n'.format(python_code_run))
        fw.close()
    set_user_grp(file_run, 'mycodo', 'mycodo')

    return python_code_run, file_run


def test_python_code(python_code_run, filename):
    """
    Function to evaluate the Python 3 code using pylint3
    :param :
    :return: tuple of (all_passed, error, mod_input) variables
    """
    success = []
    error = []

    try:
        python_code_run, file_run = create_python_file(python_code_run, filename)

        lines_code = ''
        for line_num, each_line in enumerate(python_code_run.splitlines(), 1):
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
                   'pylint3 -d I,W0621,C0103,C0111,C0301,C0327,C0410,C0413,R0201,R0903,W0201,W0612 {path}'.format(
                       path=file_run)
        cmd_out, _, cmd_status = cmd_output(cmd_test)

        message = Markup(
            '<pre>\n\n'
            'Full Python Code Input code:\n\n{code}\n\n'
            'Python Code Input code analysis:\n\n{report}'
            '</pre>'.format(
                code=lines_code.replace("<", "&lt"), report=cmd_out.decode("utf-8")))
    except Exception as err:
        cmd_status = None
        message = "Error running pylint: {}".format(err)
        error.append(message)

    if cmd_status:
        error.append("pylint returned with status: {}".format(cmd_status))

    if message:
        success.append(
            "Review your code for issues and test before putting it "
            "into a production environment.")
        success.append(message)

    return success, error
