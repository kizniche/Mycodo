"""add column activated to table relay conditional

Revision ID: 091f1ae3fd1f
Revises: 4c8aab824d21
Create Date: 2016-04-17 11:24:00.637276

"""

# revision identifiers, used by Alembic.
revision = '091f1ae3fd1f'
down_revision = '4c8aab824d21'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("relayconditional") as batch_op:
        batch_op.add_column(sa.Column('activated', sa.BOOLEAN))

def downgrade():
    with op.batch_alter_table("relayconditional") as batch_op:
        batch_op.drop_column('activated')
