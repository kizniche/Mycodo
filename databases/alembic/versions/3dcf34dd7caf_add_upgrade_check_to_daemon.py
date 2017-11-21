"""Add upgrade check to daemon

Revision ID: 3dcf34dd7caf
Revises: 321038f2e101
Create Date: 2017-11-21 09:57:36.497096

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3dcf34dd7caf'
down_revision = '321038f2e101'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("misc") as batch_op:
        batch_op.add_column(sa.Column('enable_upgrade_check', sa.Boolean))
        batch_op.add_column(sa.Column('mycodo_upgrade_available', sa.Boolean))

    with op.batch_alter_table("graph") as batch_op:
        batch_op.add_column(sa.Column('enable_xaxis_reset', sa.Boolean))

    op.execute(
        '''
        UPDATE misc
        SET enable_upgrade_check=1
        '''
    )

    op.execute(
        '''
        UPDATE misc
        SET mycodo_upgrade_available=0
        '''
    )

    op.execute(
        '''
        UPDATE graph
        SET enable_xaxis_reset=1
        '''
    )


def downgrade():
    with op.batch_alter_table("misc") as batch_op:
        batch_op.drop_column('enable_upgrade_check')
        batch_op.drop_column('mycodo_upgrade_available')

    with op.batch_alter_table("graph") as batch_op:
        batch_op.drop_column('enable_xaxis_reset')
