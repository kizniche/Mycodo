"""Add PWM and RPM Input options

Revision ID: 56ec4ceb9dfd
Revises: a0c55d19384c
Create Date: 2017-10-27 20:20:10.582102

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '56ec4ceb9dfd'
down_revision = 'a0c55d19384c'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("sensor") as batch_op:
        batch_op.add_column(sa.Column('weighting', sa.FLOAT))
        batch_op.add_column(sa.Column('rpm_pulses_per_rev', sa.FLOAT))


def downgrade():
    with op.batch_alter_table("sensor") as batch_op:
        batch_op.drop_column('weighting')
        batch_op.drop_column('rpm_pulses_per_rev')
