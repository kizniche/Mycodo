"""Add Linux Command Output option: user to execute with

Revision ID: e5bd30e798b8
Revises: 61a0d0568d24
Create Date: 2020-05-05 19:38:24.677775

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e5bd30e798b8'
down_revision = '61a0d0568d24'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("output") as batch_op:
        batch_op.add_column(sa.Column('linux_command_user', sa.Text))

    op.execute(
        '''
        UPDATE output
        SET linux_command_user="pi"
        '''
    )


def downgrade():
    with op.batch_alter_table("output") as batch_op:
        batch_op.drop_column('linux_command_user')
