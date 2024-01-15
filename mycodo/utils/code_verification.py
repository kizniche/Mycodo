# -*- coding: utf-8 -*-
import logging
import os

from markupsafe import Markup

from mycodo.config import INSTALL_DIRECTORY
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
    Function to evaluate the Python 3 code using pylint
    :param :
    :return: tuple (info, warning, success, error)
    """
    info = []
    warning = []
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

        cmd_test = 'mkdir -p /opt/Mycodo/.pylint.d && ' \
                   'export PYTHONPATH=$PYTHONPATH:/opt/Mycodo && ' \
                   'export PYLINTHOME=/opt/Mycodo/.pylint.d && ' \
                   '{dir}/env/bin/python -m pylint -d I,W0621,C0103,C0111,C0301,C0327,C0410,C0413,R0201,R0903,W0201,W0612 {path}'.format(
                    dir=INSTALL_DIRECTORY, path=file_run)
        cmd_out, _, cmd_status = cmd_output(cmd_test, user='root')

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
        warning.append("pylint returned with status: {}".format(cmd_status))

    if message:
        info.append(
            "Review your code for issues and test before putting it "
            "into a production environment.")
        info.append(message)

    return info, warning, success, error
