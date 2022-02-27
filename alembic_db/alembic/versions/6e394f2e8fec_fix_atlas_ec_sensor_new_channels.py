"""Fix Atlas EC sensor new channels

Revision ID: 6e394f2e8fec
Revises: bdc03b708ac6
Create Date: 2021-08-30 22:58:19.375813

"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))

from alembic_db.alembic_post_utils import write_revision_post_alembic

# revision identifiers, used by Alembic.
revision = '6e394f2e8fec'
down_revision = 'bdc03b708ac6'
branch_labels = None
depends_on = None


def upgrade():
    write_revision_post_alembic(revision)


def downgrade():
    pass
