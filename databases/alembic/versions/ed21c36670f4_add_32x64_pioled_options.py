"""Add 32x64 PiOLED options

Revision ID: ed21c36670f4
Revises: 82ee046fbf9b
Create Date: 2019-01-29 11:13:24.059879

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ed21c36670f4'
down_revision = '82ee046fbf9b'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("lcd_data") as batch_op:
        batch_op.add_column(sa.Column('line_5_id', sa.Text))
        batch_op.add_column(sa.Column('line_5_type', sa.Text))
        batch_op.add_column(sa.Column('line_5_measurement', sa.Text))
        batch_op.add_column(sa.Column('line_5_max_age', sa.Integer))
        batch_op.add_column(sa.Column('line_5_decimal_places', sa.Integer))

        batch_op.add_column(sa.Column('line_6_id', sa.Text))
        batch_op.add_column(sa.Column('line_6_type', sa.Text))
        batch_op.add_column(sa.Column('line_6_measurement', sa.Text))
        batch_op.add_column(sa.Column('line_6_max_age', sa.Integer))
        batch_op.add_column(sa.Column('line_6_decimal_places', sa.Integer))

        batch_op.add_column(sa.Column('line_7_id', sa.Text))
        batch_op.add_column(sa.Column('line_7_type', sa.Text))
        batch_op.add_column(sa.Column('line_7_measurement', sa.Text))
        batch_op.add_column(sa.Column('line_7_max_age', sa.Integer))
        batch_op.add_column(sa.Column('line_7_decimal_places', sa.Integer))

        batch_op.add_column(sa.Column('line_8_id', sa.Text))
        batch_op.add_column(sa.Column('line_8_type', sa.Text))
        batch_op.add_column(sa.Column('line_8_measurement', sa.Text))
        batch_op.add_column(sa.Column('line_8_max_age', sa.Integer))
        batch_op.add_column(sa.Column('line_8_decimal_places', sa.Integer))


def downgrade():
    with op.batch_alter_table("lcd_data") as batch_op:
        batch_op.drop_column('line_5_id')
        batch_op.drop_column('line_5_type')
        batch_op.drop_column('line_5_measurement')
        batch_op.drop_column('line_5_max_age')
        batch_op.drop_column('line_5_decimal_places')

        batch_op.drop_column('line_6_id')
        batch_op.drop_column('line_6_type')
        batch_op.drop_column('line_6_measurement')
        batch_op.drop_column('line_6_max_age')
        batch_op.drop_column('line_6_decimal_places')

        batch_op.drop_column('line_7_id')
        batch_op.drop_column('line_7_type')
        batch_op.drop_column('line_7_measurement')
        batch_op.drop_column('line_7_max_age')
        batch_op.drop_column('line_7_decimal_places')

        batch_op.drop_column('line_8_id')
        batch_op.drop_column('line_8_type')
        batch_op.drop_column('line_8_measurement')
        batch_op.drop_column('line_8_max_age')
        batch_op.drop_column('line_8_decimal_places')
