"""set default library for DS18B20 and DS18S20 inputs

Revision ID: b4d958997cf0
Revises: 8e5a8351ad7a
Create Date: 2019-01-07 17:16:52.340195

"""
import sys

import os

sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))

from databases.alembic_post import write_revision_post_alembic


# revision identifiers, used by Alembic.
revision = 'b4d958997cf0'
down_revision = '8e5a8351ad7a'
branch_labels = None
depends_on = None


def upgrade():
    write_revision_post_alembic(revision)


def downgrade():
    pass
