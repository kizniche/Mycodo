"""add rescale method options

Revision ID: 50a4e41e7444
Revises: 211cd8cc576b
Create Date: 2021-04-10 10:28:20.169929

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '50a4e41e7444'
down_revision = '211cd8cc576b'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("device_measurements") as batch_op:
        batch_op.add_column(sa.Column('rescale_method', sa.Text))
        batch_op.add_column(sa.Column('rescale_equation', sa.Text))

    op.execute(
        '''
        UPDATE device_measurements
        SET rescale_method='linear'
        '''
    )

    op.execute(
        '''
        UPDATE device_measurements
        SET rescale_equation='(x+2)*3'
        '''
    )


def downgrade():
    with op.batch_alter_table("device_measurements") as batch_op:
        batch_op.drop_column('rescale_method')
        batch_op.drop_column('rescale_equation')
