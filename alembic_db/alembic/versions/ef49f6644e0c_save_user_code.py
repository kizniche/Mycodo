"""Save user code

Revision ID: ef49f6644e0c
Revises: 65271370a3a9
Create Date: 2019-09-11 17:33:47.711146

"""
import sys

import os

sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))

from alembic_db.alembic_post_utils import write_revision_post_alembic

from mycodo.config import ID_FILE
from mycodo.config import STATS_CSV


# revision identifiers, used by Alembic.
revision = 'ef49f6644e0c'
down_revision = '65271370a3a9'
branch_labels = None
depends_on = None


def upgrade():
    write_revision_post_alembic(revision)

    try:
        os.remove(ID_FILE)
        os.remove(STATS_CSV)
    except:
        pass


def downgrade():
    pass
