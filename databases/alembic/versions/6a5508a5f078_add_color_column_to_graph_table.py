"""add color column to graph table

Revision ID: 6a5508a5f078
Revises: e4f984cd01d4
Create Date: 2017-01-22 19:44:27.530157

"""

# revision identifiers, used by Alembic.
revision = '6a5508a5f078'
down_revision = 'e4f984cd01d4'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table('graph') as batch_op:
        batch_op.add_column(sa.Column('colors', sa.TEXT))
        batch_op.add_column(sa.Column('colors_custom', sa.BOOLEAN))


def downgrade():
    with op.batch_alter_table('graph') as batch_op:
        batch_op.drop_column('colors')
        batch_op.drop_column('colors_custom')
