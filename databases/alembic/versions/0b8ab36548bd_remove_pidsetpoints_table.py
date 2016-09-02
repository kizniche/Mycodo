"""Remove pidsetpoints table

Revision ID: 0b8ab36548bd
Revises: 9466037ace82
Create Date: 2016-09-01 22:08:33.184379

"""

# revision identifiers, used by Alembic.
revision = '0b8ab36548bd'
down_revision = '9466037ace82'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_table('pidsetpoints')


def downgrade():
    op.create_table(
        'pidsetpoints',
        sa.Column('id', sa.TEXT,  unique=True, primary_key=True),
        sa.Column('pid_id', sa.TEXT),
        sa.Column('start_time', sa.TEXT),
        sa.Column('end_time', sa.TEXT),
        sa.Column('start_setpoint', sa.REAL),
        sa.Column('end_setpoint', sa.REAL)
    )
