"""Add flash LCD to sensor conditional

Revision ID: efa3afc7d152
Revises: b0187b98a37e
Create Date: 2016-05-11 18:14:14.783861

"""

# revision identifiers, used by Alembic.
revision = 'efa3afc7d152'
down_revision = 'b0187b98a37e'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("relayconditional") as batch_op:
        batch_op.add_column(sa.Column('flash_lcd', sa.TEXT))
    with op.batch_alter_table("sensorconditional") as batch_op:
        batch_op.add_column(sa.Column('flash_lcd', sa.TEXT))
    op.execute(
        '''
        UPDATE relayconditional
        SET flash_lcd=''
        WHERE flash_lcd IS NULL
        '''
    )
    op.execute(
        '''
        UPDATE sensorconditional
        SET flash_lcd=''
        WHERE flash_lcd IS NULL
        '''
    )

def downgrade():
    with op.batch_alter_table("relayconditional") as batch_op:
        batch_op.drop_column('flash_lcd')
    with op.batch_alter_table("sensorconditional") as batch_op:
        batch_op.drop_column('flash_lcd')
