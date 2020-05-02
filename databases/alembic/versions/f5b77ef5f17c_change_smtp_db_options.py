"""Change SMTP DB options

Revision ID: f5b77ef5f17c
Revises: 4b5f6207cbdf
Create Date: 2020-05-02 11:55:42.943143

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f5b77ef5f17c'
down_revision = '4b5f6207cbdf'
branch_labels = None
depends_on = None


def upgrade():
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))
    from databases.alembic_post_utils import write_revision_post_alembic
    write_revision_post_alembic(revision)

    with op.batch_alter_table("smtp") as batch_op:
        batch_op.add_column(sa.Column('protocol', sa.Text))


def downgrade():
    with op.batch_alter_table("smtp") as batch_op:
        batch_op.drop_column('protocol')
