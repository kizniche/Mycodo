"""Add table method for new setpoint tracking methods

Revision ID: 96d3834825f9
Revises: 22bd961f2c91
Create Date: 2016-07-30 14:07:35.278830

"""

# revision identifiers, used by Alembic.
revision = '96d3834825f9'
down_revision = '22bd961f2c91'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'method',
        sa.Column('id', sa.TEXT, unique=True, primary_key=True, nullable=False),
        sa.Column('name', sa.TEXT),
        sa.Column('method_id', sa.TEXT),
        sa.Column('method_type', sa.TEXT),
        sa.Column('method_order', sa.INT),
        sa.Column('start_time', sa.TEXT),
        sa.Column('end_time', sa.TEXT),
        sa.Column('duration_sec', sa.INT),
        sa.Column('relay_id', sa.TEXT),
        sa.Column('relay_state', sa.TEXT),
        sa.Column('relay_duration', sa.REAL),
        sa.Column('start_setpoint', sa.REAL),
        sa.Column('end_setpoint', sa.REAL)
    )

    with op.batch_alter_table("pid") as batch_op:
        batch_op.add_column(sa.Column('method_id', sa.TEXT))

    op.execute(
        '''
        UPDATE pid
        SET method_id=''
        WHERE method_id IS NULL
        '''
    )


def downgrade():
    op.drop_table('method')
    with op.batch_alter_table("pid") as batch_op:
        batch_op.drop_column('method_id')
