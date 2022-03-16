"""update function actions

Revision ID: b354722c9b8b
Revises: 56a3f39af852
Create Date: 2022-02-13 20:06:50.915088

"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))

from alembic_db.alembic_post_utils import write_revision_post_alembic


# revision identifiers, used by Alembic.
revision = 'b354722c9b8b'
down_revision = '56a3f39af852'
branch_labels = None
depends_on = None


def upgrade():
    write_revision_post_alembic(revision)


def downgrade():
    pass
