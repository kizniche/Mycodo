"""Add MAX31856 Input option thermocouple_type

Revision ID: fdb54958dd73
Revises: be8dee3eb8e5
Create Date: 2018-03-09 21:32:01.190522

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fdb54958dd73'
down_revision = 'be8dee3eb8e5'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("sensor") as batch_op:
        batch_op.add_column(sa.Column('thermocouple_type', sa.Text))
        batch_op.add_column(sa.Column('pre_relay_during_measure', sa.Boolean))


def downgrade():
    with op.batch_alter_table("sensor") as batch_op:
        batch_op.drop_column('thermocouple_type')
        batch_op.drop_column('pre_relay_during_measure')
