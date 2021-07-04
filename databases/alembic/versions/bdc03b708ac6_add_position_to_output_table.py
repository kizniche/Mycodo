"""Add position to tables

Revision ID: bdc03b708ac6
Revises: b8ff72b5c2c9
Create Date: 2021-06-29 18:28:03.951101

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bdc03b708ac6'
down_revision = 'b8ff72b5c2c9'
branch_labels = None
depends_on = None


def upgrade():
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))
    from databases.alembic_post_utils import write_revision_post_alembic
    write_revision_post_alembic(revision)

    with op.batch_alter_table("output") as batch_op:
        batch_op.add_column(sa.Column('position_y', sa.Integer))
        batch_op.add_column(sa.Column('size_y', sa.Integer))

    with op.batch_alter_table("conditional") as batch_op:
        batch_op.add_column(sa.Column('position_y', sa.Integer))

    with op.batch_alter_table("custom_controller") as batch_op:
        batch_op.add_column(sa.Column('position_y', sa.Integer))

    with op.batch_alter_table("function") as batch_op:
        batch_op.add_column(sa.Column('position_y', sa.Integer))

    with op.batch_alter_table("trigger") as batch_op:
        batch_op.add_column(sa.Column('position_y', sa.Integer))

    with op.batch_alter_table("pid") as batch_op:
        batch_op.add_column(sa.Column('position_y', sa.Integer))


def downgrade():
    with op.batch_alter_table("output") as batch_op:
        batch_op.drop_column('position_y')
        batch_op.drop_column('size_y')

    with op.batch_alter_table("conditional") as batch_op:
        batch_op.drop_column('position_y')

    with op.batch_alter_table("custom_controller") as batch_op:
        batch_op.drop_column('position_y')

    with op.batch_alter_table("function") as batch_op:
        batch_op.drop_column('position_y')

    with op.batch_alter_table("trigger") as batch_op:
        batch_op.drop_column('position_y')

    with op.batch_alter_table("pid") as batch_op:
        batch_op.drop_column('position_y')
