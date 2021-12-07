"""Add output custom_options

Revision ID: 840c4d18e38c
Revises: caf50eb4f236
Create Date: 2020-05-12 15:24:47.955952

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '840c4d18e38c'
down_revision = 'caf50eb4f236'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("output") as batch_op:
        batch_op.add_column(sa.Column('custom_options', sa.Text))
        batch_op.add_column(sa.Column('i2c_location', sa.Text))
        batch_op.add_column(sa.Column('ftdi_location', sa.Text))
        batch_op.add_column(sa.Column('uart_location', sa.Text))


def downgrade():
    with op.batch_alter_table("output") as batch_op:
        batch_op.drop_column('custom_options')
        batch_op.drop_column('i2c_location')
        batch_op.drop_column('ftdi_location')
        batch_op.drop_column('uart_location')
