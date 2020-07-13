"""Add new output options

Revision ID: af5891792291
Revises: 561621f634cb
Create Date: 2020-07-06 18:31:35.210777

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'af5891792291'
down_revision = '561621f634cb'
branch_labels = None
depends_on = None


def upgrade():
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))
    from databases.alembic_post_utils import write_revision_post_alembic
    write_revision_post_alembic(revision)

    with op.batch_alter_table("function_actions") as batch_op:
        batch_op.add_column(sa.Column('do_output_amount', sa.Float))

    with op.batch_alter_table("pid") as batch_op:
        batch_op.add_column(sa.Column('raise_output_type', sa.String))
        batch_op.add_column(sa.Column('lower_output_type', sa.String))


def downgrade():
    with op.batch_alter_table("function_actions") as batch_op:
        batch_op.drop_column('do_output_amount')

    with op.batch_alter_table("pid") as batch_op:
        batch_op.drop_column('raise_output_type')
        batch_op.drop_column('lower_output_type')
