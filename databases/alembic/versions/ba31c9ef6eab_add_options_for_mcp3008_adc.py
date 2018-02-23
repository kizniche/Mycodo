"""Add options for MCP3008 ADC

Revision ID: ba31c9ef6eab
Revises: 1031452acfc9
Create Date: 2018-02-23 12:04:14.534345

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ba31c9ef6eab'
down_revision = '1031452acfc9'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("sensor") as batch_op:
        batch_op.add_column(sa.Column('pin_clock', sa.Integer))
        batch_op.add_column(sa.Column('pin_cs', sa.Integer))
        batch_op.add_column(sa.Column('pin_mosi', sa.Integer))
        batch_op.add_column(sa.Column('pin_miso', sa.Integer))


def downgrade():
    with op.batch_alter_table("sensor") as batch_op:
        batch_op.drop_column('pin_clock')
        batch_op.drop_column('pin_cs')
        batch_op.drop_column('pin_mosi')
        batch_op.drop_column('pin_miso')
