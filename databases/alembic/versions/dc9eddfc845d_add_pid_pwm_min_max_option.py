"""add PID PWM min-max option

Revision ID: dc9eddfc845d
Revises: a91e6a71028f
Create Date: 2020-03-16 15:07:10.498454

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dc9eddfc845d'
down_revision = 'a91e6a71028f'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("pid") as batch_op:
        batch_op.add_column(sa.Column('raise_always_min_pwm', sa.Boolean))
        batch_op.add_column(sa.Column('lower_always_min_pwm', sa.Boolean))


def downgrade():
    with op.batch_alter_table("pid") as batch_op:
        batch_op.drop_column('raise_always_min_pwm')
        batch_op.drop_column('lower_always_min_pwm')
