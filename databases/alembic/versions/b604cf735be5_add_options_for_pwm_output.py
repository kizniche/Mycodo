"""add options for PWM output

Revision ID: b604cf735be5
Revises: 9d7631079ac1
Create Date: 2017-07-16 17:03:02.586020

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b604cf735be5'
down_revision = '9d7631079ac1'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("relay") as batch_op:
        batch_op.add_column(sa.Column('pwm_hertz', sa.INTEGER))

    with op.batch_alter_table("pid") as batch_op:
        batch_op.add_column(sa.Column('pid_type', sa.INTEGER))

    op.execute(
        '''
        UPDATE pid
        SET pid_type='relay'
        WHERE pid_type IS NULL
        '''
    )


def downgrade():
    with op.batch_alter_table("relay") as batch_op:
        batch_op.drop_column('pwm_hertz')

    with op.batch_alter_table("pid") as batch_op:
        batch_op.drop_column('pid_type')
