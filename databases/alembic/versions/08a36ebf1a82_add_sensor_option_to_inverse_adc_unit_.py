"""Add Sensor option to inverse ADC unit scale

Revision ID: 08a36ebf1a82
Revises: ca975c26965c
Create Date: 2017-10-23 19:30:58.501329

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '08a36ebf1a82'
down_revision = 'ca975c26965c'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("sensor") as batch_op:
        batch_op.add_column(sa.Column('adc_inverse_unit_scale', sa.BOOLEAN))


def downgrade():
    with op.batch_alter_table("sensor") as batch_op:
        batch_op.drop_column('adc_inverse_unit_scale')
