"""Add new Script PID type

Revision ID: 4598c6575d45
Revises: 25676b9d5856
Create Date: 2017-10-18 21:49:18.144274

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4598c6575d45'
down_revision = '25676b9d5856'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("pid") as batch_op:
        batch_op.add_column(sa.Column('pid_type_input', sa.TEXT))
        batch_op.add_column(sa.Column('measurement_cmd', sa.TEXT))

    op.execute(
        '''
        UPDATE pid
        SET pid_type_input='sensor'
        WHERE pid_type_input IS NULL
        '''
    )


def downgrade():
    with op.batch_alter_table("pid") as batch_op:
        batch_op.drop_column('pid_type_input')
        batch_op.drop_column('measurement_cmd')
