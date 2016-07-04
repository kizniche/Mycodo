"""Add pid_id to graph table for graphing setpoints

Revision ID: b0187b98a37e
Revises: 44e819a57fcb
Create Date: 2016-05-08 13:37:27.277321

"""

# revision identifiers, used by Alembic.
revision = 'b0187b98a37e'
down_revision = '44e819a57fcb'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("graph") as batch_op:
        batch_op.add_column(sa.Column('pid_ids', sa.TEXT))
    op.execute(
        '''
        UPDATE graph
        SET pid_ids=''
        WHERE pid_ids IS NULL
        '''
    )

def downgrade():
    with op.batch_alter_table("graph") as batch_op:
        batch_op.drop_column('pid_ids')
