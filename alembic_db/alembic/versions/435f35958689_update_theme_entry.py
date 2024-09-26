"""update theme entry

Revision ID: 435f35958689
Revises: 9bdb60d2a2cd
Create Date: 2024-09-26 17:18:03.518493

"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))

from alembic_db.alembic_post_utils import write_revision_post_alembic

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '435f35958689'
down_revision = '9bdb60d2a2cd'
branch_labels = None
depends_on = None


def upgrade():
    write_revision_post_alembic(revision)


def downgrade():
    pass
