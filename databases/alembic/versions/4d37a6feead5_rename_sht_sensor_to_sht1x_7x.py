"""Rename SHT sensor to SHT1x_7x

Revision ID: 4d37a6feead5
Revises: dba0087357cd
Create Date: 2016-07-19 16:22:25.091105

"""

# revision identifiers, used by Alembic.
revision = '4d37a6feead5'
down_revision = 'dba0087357cd'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute(
        '''
        UPDATE sensor
        SET device='SHT1x_7x'
        WHERE device == 'SHT'
        '''
    )


def downgrade():
    op.execute(
        '''
        UPDATE sensor
        SET device='SHT'
        WHERE device == 'SHT1x_7x'
        '''
    )
