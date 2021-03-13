"""remove conversion entry

Revision ID: 110d2d00e91d
Revises: 24dbd0b8c8d1
Create Date: 2021-03-13 16:52:45.328919

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '110d2d00e91d'
down_revision = '24dbd0b8c8d1'
branch_labels = None
depends_on = None


def upgrade():
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))
    from databases.alembic_post_utils import write_revision_post_alembic
    write_revision_post_alembic(revision)

def downgrade():
    pass
