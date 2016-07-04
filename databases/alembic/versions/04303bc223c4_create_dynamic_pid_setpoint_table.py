"""create dynamic PID setpoint table

Revision ID: 04303bc223c4
Revises: 5d5a7158bfe2
Create Date: 2016-05-01 18:11:43.296519

"""

# revision identifiers, used by Alembic.
revision = '04303bc223c4'
down_revision = '5d5a7158bfe2'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'pidsetpoints',
        sa.Column('id', sa.TEXT, unique=True, primary_key=True, nullable=False),
        sa.Column('pid_id', sa.TEXT),
        sa.Column('start_time', sa.TEXT),
        sa.Column('end_time', sa.TEXT),
        sa.Column('start_setpoint', sa.REAL),
        sa.Column('end_setpoint', sa.REAL),
    )


def downgrade():
    op.drop_table('pidsetpoints')
