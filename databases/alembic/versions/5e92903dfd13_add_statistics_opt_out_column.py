"""Add statistics opt-out column

Revision ID: 5e92903dfd13
Revises: 091f1ae3fd1f
Create Date: 2016-04-18 19:16:27.183472

"""

# revision identifiers, used by Alembic.
revision = '5e92903dfd13'
down_revision = '091f1ae3fd1f'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("misc") as batch_op:
        batch_op.add_column(sa.Column('stats_opt_out', sa.BOOLEAN))

def downgrade():
    with op.batch_alter_table("misc") as batch_op:
        batch_op.drop_column('stats_opt_out')
