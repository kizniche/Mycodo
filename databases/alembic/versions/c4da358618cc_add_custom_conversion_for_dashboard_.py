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

    with op.batch_alter_table("pid") as batch_op:
        batch_op.add_column(sa.Column('store_lower_as_negative', sa.Boolean))

    with op.batch_alter_table("conditional") as batch_op:
        batch_op.add_column(sa.Column('rise_or_set', sa.Text))
        batch_op.add_column(sa.Column('latitude', sa.Float))
        batch_op.add_column(sa.Column('longitude', sa.Float))
        batch_op.add_column(sa.Column('zenith', sa.Float))
        batch_op.add_column(sa.Column('date_offset_days', sa.Integer))
        batch_op.add_column(sa.Column('time_offset_minutes', sa.Integer))

    op.execute(
        '''
        UPDATE sensor
        SET convert_to_unit=''
        '''
    )

    op.execute(
        '''
        UPDATE pid
        SET store_lower_as_negative=1
        '''
    )


def downgrade():
    with op.batch_alter_table("sensor") as batch_op:
        batch_op.drop_column('convert_to_unit')

    with op.batch_alter_table("pid") as batch_op:
        batch_op.drop_column('store_lower_as_negative')

    with op.batch_alter_table("conditional") as batch_op:
        batch_op.drop_column('rise_or_set')
        batch_op.drop_column('latitude')
        batch_op.drop_column('longitude')
        batch_op.drop_column('zenith')
        batch_op.drop_column('date_offset_days')
        batch_op.drop_column('time_offset_minutes')
