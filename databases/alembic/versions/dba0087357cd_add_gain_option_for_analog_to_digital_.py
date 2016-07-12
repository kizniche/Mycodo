"""Add gain option for analog to digital converters

Revision ID: dba0087357cd
Revises: 24f75895d28e
Create Date: 2016-07-12 17:14:52.053996

"""

# revision identifiers, used by Alembic.
revision = 'dba0087357cd'
down_revision = '24f75895d28e'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("sensor") as batch_op:
        batch_op.add_column(sa.Column('adc_gain', sa.INT))
    op.execute(
        '''
        UPDATE sensor
        SET adc_gain=1
        WHERE adc_gain IS NULL
        '''
    )

def downgrade():
    with op.batch_alter_table("sensor") as batch_op:
        batch_op.drop_column('adc_gain')
