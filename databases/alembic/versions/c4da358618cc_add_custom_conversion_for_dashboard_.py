"""Add custom conversion for dashboard elements

Revision ID: c4da358618cc
Revises: 01ba9473fc96
Create Date: 2018-04-01 16:13:51.077879

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c4da358618cc'
down_revision = '01ba9473fc96'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("sensor") as batch_op:
        batch_op.add_column(sa.Column('convert_to_unit', sa.Text))

    op.execute(
        '''
        UPDATE sensor
        SET convert_to_unit=''
        '''
    )


def downgrade():
    with op.batch_alter_table("sensor") as batch_op:
        batch_op.drop_column('convert_to_unit')
