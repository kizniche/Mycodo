"""Add PID option send_negative_amount

Revision ID: d46e17d65f48
Revises: 4fedeb57e75b
Create Date: 2021-05-10 18:47:02.316732

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd46e17d65f48'
down_revision = '4fedeb57e75b'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("pid") as batch_op:
        batch_op.add_column(sa.Column('send_lower_as_negative', sa.Boolean))

    op.execute(
        '''
        UPDATE pid
        SET send_lower_as_negative=0
        '''
    )


def downgrade():
    with op.batch_alter_table("pid") as batch_op:
        batch_op.drop_column('send_lower_as_negative')
