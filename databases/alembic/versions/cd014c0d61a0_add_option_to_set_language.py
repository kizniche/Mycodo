"""Add option to set language

Revision ID: cd014c0d61a0
Revises: 52aeaa701dfb
Create Date: 2017-01-06 17:22:02.598082

"""

# revision identifiers, used by Alembic.
revision = 'cd014c0d61a0'
down_revision = '52aeaa701dfb'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("misc") as batch_op:
        batch_op.add_column(sa.Column('language', sa.TEXT))


def downgrade():
    with op.batch_alter_table("misc") as batch_op:
        batch_op.drop_column('language')

