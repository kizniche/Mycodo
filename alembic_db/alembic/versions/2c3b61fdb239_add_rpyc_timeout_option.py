"""Add rpyc_timeout option

Revision ID: 2c3b61fdb239
Revises: b08ffb575d36
Create Date: 2019-05-21 13:51:05.086250

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2c3b61fdb239'
down_revision = 'b08ffb575d36'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("misc") as batch_op:
        batch_op.add_column(sa.Column('rpyc_timeout', sa.Integer))

    with op.batch_alter_table("output") as batch_op:
        batch_op.add_column(sa.Column('off_until', sa.DateTime))

    op.execute(
        '''
        UPDATE misc
        SET rpyc_timeout=30
        '''
    )


def downgrade():
    with op.batch_alter_table("misc") as batch_op:
        batch_op.drop_column('rpyc_timeout')

    with op.batch_alter_table("output") as batch_op:
        batch_op.drop_column('off_until')
