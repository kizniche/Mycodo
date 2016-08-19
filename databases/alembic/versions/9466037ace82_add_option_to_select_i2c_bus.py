"""add option to select i2c bus

Revision ID: 9466037ace82
Revises: 96d3834825f9
Create Date: 2016-08-18 19:07:27.775959

"""

# revision identifiers, used by Alembic.
revision = '9466037ace82'
down_revision = '96d3834825f9'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("sensor") as batch_op:
        batch_op.add_column(sa.Column('i2c_bus', sa.INT))
        batch_op.add_column(sa.Column('multiplexer_bus', sa.INT))

    op.execute(
        '''
        UPDATE sensor
        SET i2c_bus=1
        WHERE i2c_bus IS NULL
        '''
    )

    op.execute(
        '''
        UPDATE sensor
        SET multiplexer_bus=1
        WHERE multiplexer_bus IS NULL
        '''
    )


def downgrade():
    with op.batch_alter_table("sensor") as batch_op:
        batch_op.drop_column('i2c_bus')
        batch_op.drop_column('multiplexer_bus')
