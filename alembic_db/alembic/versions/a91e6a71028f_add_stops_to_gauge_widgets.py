"""Add stops to gauge widgets

Revision ID: a91e6a71028f
Revises: 0a8a5eb1be4b
Create Date: 2020-02-20 19:57:28.886276

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a91e6a71028f'
down_revision = '0a8a5eb1be4b'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("widget") as batch_op:
        batch_op.add_column(sa.Column('stops', sa.Integer))

    op.execute(
        '''
        UPDATE widget
        SET stops=4
        '''
    )


def downgrade():
    with op.batch_alter_table("widget") as batch_op:
        batch_op.drop_column('stops')
