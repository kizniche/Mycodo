"""add MH-Z19 CO2 sensor

Revision ID: c7b4a120a7bb
Revises: b604cf735be5
Create Date: 2017-08-06 12:14:33.707029

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c7b4a120a7bb'
down_revision = 'b604cf735be5'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        '''
        UPDATE sensor
        SET interface='UART'
        WHERE device IS 'K30'
        '''
    )

    op.execute(
        '''
        UPDATE sensor
        SET device='K30_UART'
        WHERE device IS 'K30'
        '''
    )


def downgrade():
    op.execute(
        '''
        UPDATE sensor
        SET interface=NULL
        WHERE device IS 'K30_UART'
        '''
    )

    op.execute(
        '''
        UPDATE sensor
        SET device='K30'
        WHERE device IS 'K30_UART'
        '''
    )
