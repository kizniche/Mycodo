"""Add Action: ramp PWM

Revision ID: 0bd51c536217
Revises: 4b619edb9a8f
Create Date: 2019-10-22 09:42:44.942012

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0bd51c536217'
down_revision = '4b619edb9a8f'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("function_actions") as batch_op:
        batch_op.add_column(sa.Column('do_output_pwm2', sa.Float))

    op.execute(
        '''
        UPDATE function_actions
        SET do_output_pwm2=0
        '''
    )


def downgrade():
    with op.batch_alter_table("function_actions") as batch_op:
        batch_op.drop_column('do_output_pwm2')
