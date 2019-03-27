"""Add TTN options

Revision ID: f9ddbe510462
Revises: 27e1eca963ab
Create Date: 2019-03-25 14:28:23.548877

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f9ddbe510462'
down_revision = '27e1eca963ab'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("input") as batch_op:
        batch_op.add_column(sa.Column('num_channels', sa.Integer))

    with op.batch_alter_table("conditional_data") as batch_op:
        batch_op.add_column(sa.Column('output_id', sa.Text))


def downgrade():
    with op.batch_alter_table("input") as batch_op:
        batch_op.drop_column('num_channels')

    with op.batch_alter_table("conditional_data") as batch_op:
        batch_op.drop_column('output_id')
