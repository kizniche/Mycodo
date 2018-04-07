"""Add invert PWM option

Revision ID: d881bacc5814
Revises: c4da358618cc
Create Date: 2018-04-07 12:00:39.231553

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd881bacc5814'
down_revision = 'c4da358618cc'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("relay") as batch_op:
        batch_op.add_column(sa.Column('pwm_invert_signal', sa.Boolean))

    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column('landing_page', sa.Text))

    op.execute(
        '''
        UPDATE relay
        SET pwm_invert_signal=0
        '''
    )

    op.execute(
        '''
        UPDATE users
        SET landing_page='live'
        '''
    )


def downgrade():
    with op.batch_alter_table("relay") as batch_op:
        batch_op.drop_column('pwm_invert_signal')

    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column('landing_page')
