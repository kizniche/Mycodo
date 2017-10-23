"""Add LCD I2C bus option

Revision ID: ca975c26965c
Revises: 66db29288333
Create Date: 2017-10-22 22:09:05.709139

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ca975c26965c'
down_revision = '66db29288333'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("lcd") as batch_op:
        batch_op.add_column(sa.Column('i2c_bus', sa.INTEGER))

    op.execute(
        '''
        UPDATE lcd
        SET i2c_bus=1
        WHERE i2c_bus IS NULL
        '''
    )


def downgrade():
    with op.batch_alter_table("lcd") as batch_op:
        batch_op.drop_column('i2c_bus')
