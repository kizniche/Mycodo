"""Save user code

Revision ID: ef49f6644e0c
Revises: 65271370a3a9
Create Date: 2019-09-11 17:33:47.711146

"""
import sys
import textwrap

import os

sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))

from mycodo.databases.models import Actions
from mycodo.databases.models import Conditional
from mycodo.databases.models import ConditionalConditions
from mycodo.databases.models import Input
from mycodo.databases.utils import session_scope
from mycodo.config import PATH_PYTHON_CODE_USER
from mycodo.config import SQL_DATABASE_MYCODO
from mycodo.config import ID_FILE
from mycodo.config import STATS_CSV
from mycodo.inputs.python_code import execute_at_creation
from mycodo.mycodo_flask.utils.utils_misc import pre_statement_run
from mycodo.utils.system_pi import assure_path_exists


# revision identifiers, used by Alembic.
revision = 'ef49f6644e0c'
down_revision = '65271370a3a9'
branch_labels = None
depends_on = None

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO


def cond_statement_replace(cond_statement):
    """Replace short condition/action IDs in conditional statement with full condition/action IDs"""
    cond_statement_replaced = cond_statement
    with session_scope(MYCODO_DB_PATH) as conditional_sess:
        for each_condition in conditional_sess.query(ConditionalConditions).all():
            condition_id_short = each_condition.unique_id.split('-')[0]
            cond_statement_replaced = cond_statement_replaced.replace(
                '{{{id}}}'.format(id=condition_id_short),
                each_condition.unique_id)

        for each_action in conditional_sess.query(Actions).all():
            action_id_short = each_action.unique_id.split('-')[0]
            cond_statement_replaced = cond_statement_replaced.replace(
                '{{{id}}}'.format(id=action_id_short),
                each_action.unique_id)

        conditional_sess.expunge_all()
        conditional_sess.close()

    return cond_statement_replaced


def upgrade():
    with session_scope(MYCODO_DB_PATH) as conditional_sess:
        for each_conditional in conditional_sess.query(Conditional).all():
            try:
                indented_code = textwrap.indent(
                    each_conditional.conditional_statement, ' ' * 8)

                cond_statement_run = pre_statement_run + indented_code
                cond_statement_run = cond_statement_replace(cond_statement_run)

                assure_path_exists(PATH_PYTHON_CODE_USER)
                file_run = '{}/conditional_{}.py'.format(
                    PATH_PYTHON_CODE_USER, each_conditional.unique_id)
                with open(file_run, 'w') as fw:
                    fw.write('{}\n'.format(cond_statement_run))
                    fw.close()
            except Exception as msg:
                print("Exception: {}".format(msg))

            # Inputs
        with session_scope(MYCODO_DB_PATH) as input_sess:
            for each_input in input_sess.query(Input).all():
                if each_input.device == 'PythonCode' and each_input.cmd_command:
                    try:
                        execute_at_creation(each_input.unique_id,
                                            each_input.cmd_command,
                                            None)
                    except Exception as msg:
                        print("Exception: {}".format(msg))

    try:
        os.remove(ID_FILE)
        os.remove(STATS_CSV)
    except:
        pass

def downgrade():
    pass
