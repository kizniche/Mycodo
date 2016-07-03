"""Add column timer to table displayorder

Revision ID: 4c8aab824d21
Revises: 
Create Date: 2016-04-14 17:26:47.050662

"""

# revision identifiers, used by Alembic.
revision = '4c8aab824d21'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("displayorder") as batch_op:
        batch_op.add_column(sa.Column('timer', sa.TEXT))

def downgrade():
    with op.batch_alter_table("displayorder") as batch_op:
        batch_op.drop_column('timer')
