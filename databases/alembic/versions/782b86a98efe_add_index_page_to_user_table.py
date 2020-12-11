"""add index_page to user table

Revision ID: 782b86a98efe
Revises: 66e27f22b15a
Create Date: 2020-11-27 10:23:41.974791

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '782b86a98efe'
down_revision = '66e27f22b15a'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column('index_page', sa.String))

    op.execute(
        '''
        UPDATE users
        SET index_page='info'
        '''
    )


def downgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column('index_page')

