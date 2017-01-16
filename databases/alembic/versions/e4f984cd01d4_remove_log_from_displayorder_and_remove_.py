"""Remove log from displayorder and remove log table

Revision ID: e4f984cd01d4
Revises: cd014c0d61a0
Create Date: 2017-01-16 11:51:19.476414

"""

# revision identifiers, used by Alembic.
revision = 'e4f984cd01d4'
down_revision = 'cd014c0d61a0'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("displayorder") as batch_op:
        batch_op.drop_column('log')

    op.drop_table('log')


def downgrade():
    with op.batch_alter_table("displayorder") as batch_op:
        batch_op.add_column(sa.Column('log', sa.TEXT))

    op.create_table(
        'log',
        sa.Column('id', sa.TEXT,  unique=True, primary_key=True),
        sa.Column('name', sa.TEXT),
        sa.Column('sensor_id', sa.TEXT),
        sa.Column('measure_type', sa.TEXT),
        sa.Column('activated', sa.INT),
        sa.Column('period', sa.INT)
    )
