"""Fix 1WIRE inputs

Revision ID: 74287a59f98a
Revises: 35b1d7df0643
Create Date: 2018-09-17 14:01:56.474744

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
revision = '74287a59f98a'
down_revision = '35b1d7df0643'
branch_labels = None
depends_on = None


def upgrade():
    with session_scope(MYCODO_DB_PATH) as new_session:
        for each_input in new_session.query(Input).all():
            if each_input.device in ['DS28EA00', 'DS1825', 'DS18B20',
                                     'DS18S20', 'MAX31850K', 'DS1822']:
                each_input.interface = '1WIRE'
        new_session.commit()


def downgrade():
    pass
