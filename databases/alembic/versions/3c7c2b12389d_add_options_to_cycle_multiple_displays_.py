"""Add options to cycle multiple displays on one LCD

Revision ID: 3c7c2b12389d
Revises: 70b7016e107f
Create Date: 2017-11-12 15:23:29.145929

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3c7c2b12389d'
down_revision = '70b7016e107f'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("lcd") as batch_op:
        batch_op.drop_column('line_1_sensor_id')
        batch_op.drop_column('line_1_measurement')
        batch_op.drop_column('line_2_sensor_id')
        batch_op.drop_column('line_2_measurement')
        batch_op.drop_column('line_3_sensor_id')
        batch_op.drop_column('line_3_measurement')
        batch_op.drop_column('line_4_sensor_id')
        batch_op.drop_column('line_4_measurement')

    op.execute(
        '''
        UPDATE lcd
        SET is_activated=0
        '''
    )

    op.create_table(
        'lcd_data',
        sa.Column('id', sa.Integer, nullable=False, unique=True),
        sa.Column('lcd_id', sa.Integer, sa.ForeignKey('lcd.id')),
        sa.Column('line_1_id', sa.Text),
        sa.Column('line_1_type', sa.Text),
        sa.Column('line_1_measurement', sa.Text),
        sa.Column('line_2_id', sa.Text),
        sa.Column('line_2_type', sa.Text),
        sa.Column('line_2_measurement', sa.Text),
        sa.Column('line_3_id', sa.Text),
        sa.Column('line_3_type', sa.Text),
        sa.Column('line_3_measurement', sa.Text),
        sa.Column('line_4_id', sa.Text),
        sa.Column('line_4_type', sa.Text),
        sa.Column('line_4_measurement', sa.Text),
        sa.PrimaryKeyConstraint('id'),
        keep_existing=True)


def downgrade():
    op.drop_table('lcd_data')

    with op.batch_alter_table("lcd") as batch_op:
        batch_op.add_column('line_1_sensor_id', sa.Text)
        batch_op.add_column('line_1_measurement', sa.Text)
        batch_op.add_column('line_2_sensor_id', sa.Text)
        batch_op.add_column('line_2_measurement', sa.Text)
        batch_op.add_column('line_3_sensor_id', sa.Text)
        batch_op.add_column('line_3_measurement', sa.Text)
        batch_op.add_column('line_4_sensor_id', sa.Text)
        batch_op.add_column('line_4_measurement', sa.Text)
