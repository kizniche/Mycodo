"""Add missing output device measurements

Revision ID: 561621f634cb
Revises: 840c4d18e38c
Create Date: 2020-06-06 14:30:07.010509

"""

# revision identifiers, used by Alembic.
revision = '561621f634cb'
down_revision = '840c4d18e38c'
branch_labels = None
depends_on = None


def upgrade():
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))
    from alembic_db.alembic_post_utils import write_revision_post_alembic
    write_revision_post_alembic(revision)


def downgrade():
    pass
