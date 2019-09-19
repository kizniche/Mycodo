"""Add conditional_data schema

Revision ID: 545744b31813
Revises: 802cc65f734e
Create Date: 2019-09-19 11:45:42.298473

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '545744b31813'
down_revision = '802cc65f734e'
branch_labels = None
depends_on = None


def upgrade():
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))
    from databases.alembic_post import write_revision_post_alembic
    write_revision_post_alembic(revision)

    with op.batch_alter_table("conditional_data") as batch_op:
        batch_op.add_column(sa.Column('controller_id', sa.Text))


def downgrade():
    with op.batch_alter_table("conditional_data") as batch_op:
        batch_op.drop_column('controller_id')
