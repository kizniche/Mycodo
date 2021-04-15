"""add function sample rate

Revision ID: 4fedeb57e75b
Revises: 50a4e41e7444
Create Date: 2021-04-14 21:12:10.313734

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4fedeb57e75b'
down_revision = '50a4e41e7444'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("misc") as batch_op:
        batch_op.add_column(sa.Column('sample_rate_controller_function', sa.Float))

    op.execute(
        '''
        UPDATE misc
        SET sample_rate_controller_function=0.25
        '''
    )


def downgrade():
    with op.batch_alter_table("misc") as batch_op:
        batch_op.drop_column('sample_rate_controller_function')
