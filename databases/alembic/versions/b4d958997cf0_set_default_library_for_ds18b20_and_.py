"""set default library for DS18B20 and DS18S20 inputs

Revision ID: b4d958997cf0
Revises: 8e5a8351ad7a
Create Date: 2019-01-07 17:16:52.340195

"""
import sys

import os

sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))

from mycodo.databases.models import Input
from mycodo.databases.utils import session_scope
from mycodo.config import SQL_DATABASE_MYCODO

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO


# revision identifiers, used by Alembic.
revision = 'b4d958997cf0'
down_revision = '8e5a8351ad7a'
branch_labels = None
depends_on = None


def upgrade():
    with session_scope(MYCODO_DB_PATH) as new_session:
        for each_input in new_session.query(Input).all():
            if each_input.device in ['DS18B20', 'DS18S20']:
                if 'library' not in each_input.custom_options:
                    if each_input.custom_options in [None, '']:
                        each_input.custom_options = 'library,w1thermsensor'
                    else:
                        each_input.custom_options += ';library,w1thermsensor'

        new_session.commit()


def downgrade():
    pass
