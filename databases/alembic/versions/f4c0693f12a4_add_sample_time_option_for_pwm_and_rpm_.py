"""Add sample time option for PWM and RPM Inputs

Revision ID: f4c0693f12a4
Revises: 56ec4ceb9dfd
Create Date: 2017-10-29 17:29:04.779324

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f4c0693f12a4'
down_revision = '56ec4ceb9dfd'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("sensor") as batch_op:
        batch_op.add_column(sa.Column('sample_time', sa.FLOAT))


def downgrade():
    with op.batch_alter_table("sensor") as batch_op:
        batch_op.drop_column('sample_time')
