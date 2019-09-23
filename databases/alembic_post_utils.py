# -*- coding: utf-8 -*-
#
# alembic_post_utils.py - Helper functions for alembic_post.py
#
import sys
import textwrap

import os

sys.path.append(os.path.abspath(os.path.join(__file__, "../..")))

from mycodo.config import ALEMBIC_UPGRADE_POST
from mycodo.config import PATH_PYTHON_CODE_USER
from mycodo.config import SQL_DATABASE_MYCODO
from mycodo.databases.models import Actions
from mycodo.databases.models import Conditional
from mycodo.databases.models import ConditionalConditions
from mycodo.databases.utils import session_scope
from mycodo.mycodo_flask.utils.utils_misc import pre_statement_run
from mycodo.utils.system_pi import assure_path_exists

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO


def read_revision_file():
    try:
        with open(ALEMBIC_UPGRADE_POST, 'r') as fd:
            return fd.read().splitlines()
    except Exception:
        return []


def write_revision_post_alembic(revision):
    with open(ALEMBIC_UPGRADE_POST, 'a') as versions_file:
        versions_file.write('{}\n'.format(revision))


def cond_statement_replace(cond_statement):
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


def save_conditional_code():
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
