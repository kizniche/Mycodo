"""Add ADC Sample Rate

Revision ID: 1421f1a02f25
Revises: 51a95b98597e
Create Date: 2018-10-08 15:44:50.265137

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1421f1a02f25'
down_revision = '51a95b98597e'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("input") as batch_op:
        batch_op.add_column(sa.Column('adc_sample_speed', sa.Text))


def downgrade():
    with op.batch_alter_table("input") as batch_op:
        batch_op.drop_column('adc_sample_speed')
