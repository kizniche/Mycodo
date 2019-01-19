"""Update Conditional Statements for new functionality

Revision ID: 70c828e05255
Revises: 0797d251d77d
Create Date: 2019-01-18 19:11:51.806582

"""
import sys

import os

sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))

from mycodo.databases.models import Conditional
from mycodo.databases.models import ConditionalConditions
from mycodo.databases.utils import session_scope
from mycodo.config import SQL_DATABASE_MYCODO

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO

# revision identifiers, used by Alembic.
revision = '70c828e05255'
down_revision = '0797d251d77d'
branch_labels = None
depends_on = None


def upgrade():
    with session_scope(MYCODO_DB_PATH) as conditional_sess:
        for each_conditional in conditional_sess.query(Conditional).all():
            if each_conditional.conditional_statement:

                # Get conditions for this conditional
                with session_scope(MYCODO_DB_PATH) as condition_sess:
                    for each_condition in condition_sess.query(ConditionalConditions).all():
                        # Test if replacement of condition ID to function needs to occur
                        id_str = '{{{id}}}'.format(id=each_condition.unique_id.split('-')[0])
                        new_str = 'measure("{{{id}}}")'.format(id=each_condition.unique_id.split('-')[0])
                        if id_str in each_conditional.conditional_statement:
                            each_conditional.conditional_statement = each_conditional.conditional_statement.replace(id_str, new_str)

        conditional_sess.commit()


def downgrade():
    pass
