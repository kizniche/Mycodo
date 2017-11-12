"""Add user language option and delete misc language option

Revision ID: 70b7016e107f
Revises: 589ab40606d3
Create Date: 2017-11-11 19:31:37.486818

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '70b7016e107f'
down_revision = '589ab40606d3'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column('language', sa.TEXT))

    with op.batch_alter_table("misc") as batch_op:
        batch_op.drop_column('language')


def downgrade():
    with op.batch_alter_table("misc") as batch_op:
        batch_op.add_column(sa.Column('language', sa.TEXT))

    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column('language')
