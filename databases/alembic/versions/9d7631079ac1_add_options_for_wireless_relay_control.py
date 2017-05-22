"""Add options for wireless relay control

Revision ID: 9d7631079ac1
Revises: a1fcd7a4adf2
Create Date: 2017-05-21 19:21:06.793135

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9d7631079ac1'
down_revision = 'a1fcd7a4adf2'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("relay") as batch_op:
        batch_op.add_column(sa.Column('relay_type', sa.Text))
        batch_op.add_column(sa.Column('protocol', sa.Integer))
        batch_op.add_column(sa.Column('pulse_length', sa.Integer))
        batch_op.add_column(sa.Column('bit_length', sa.Integer))
        batch_op.add_column(sa.Column('on_command', sa.Text))
        batch_op.add_column(sa.Column('off_command', sa.Text))
    op.execute(
        '''
        UPDATE relay
        SET relay_type='wired'
        WHERE relay_type IS NULL
        '''
    )


def downgrade():
    with op.batch_alter_table("relay") as batch_op:
        batch_op.drop_column('relay_type')
        batch_op.drop_column('protocol')
        batch_op.drop_column('pulse_length')
        batch_op.drop_column('bit_length')
        batch_op.drop_column('on_command')
        batch_op.drop_column('off_command')
