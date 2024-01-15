"""delete env

Revision ID: 4c77262f15ea
Revises: 16b28ef31b5b
Create Date: 2024-01-14 19:18:37.767591

"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))

from alembic_db.alembic_post_utils import write_revision_post_alembic

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4c77262f15ea'
down_revision = '16b28ef31b5b'
branch_labels = None
depends_on = None


def upgrade():
    write_revision_post_alembic(revision)


def downgrade():
    pass
