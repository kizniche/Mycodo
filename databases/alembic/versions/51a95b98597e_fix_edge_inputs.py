"""Fix EDGE inputs

Revision ID: 51a95b98597e
Revises: 74287a59f98a
Create Date: 2018-09-17 14:54:53.142317

"""
import sys

import os
import sqlalchemy as sa
from alembic import op

sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))

from mycodo.databases.models import Input
from mycodo.databases.utils import session_scope
from mycodo.config import SQL_DATABASE_MYCODO

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO

# revision identifiers, used by Alembic.
revision = '51a95b98597e'
down_revision = '74287a59f98a'
branch_labels = None
depends_on = None


def upgrade():
    with session_scope(MYCODO_DB_PATH) as new_session:
        for each_input in new_session.query(Input).all():
            if each_input.device == 'EDGE':
                try:
                    each_input.gpio_location = int(each_input.location)
                except:
                    pass
        new_session.commit()


def downgrade():
    pass
