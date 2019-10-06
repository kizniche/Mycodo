"""Change start/stop state from bool to str

Revision ID: b6e332156961
Revises: a6ec4e059470
Create Date: 2019-10-06 13:11:35.264054

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b6e332156961'
down_revision = 'a6ec4e059470'
branch_labels = None
depends_on = None


def upgrade():
    # import sys
    # import os
    # sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))
    # from databases.alembic_post_utils import write_revision_post_alembic
    # write_revision_post_alembic(revision)

    with op.batch_alter_table("output") as batch_op:
        batch_op.add_column(sa.Column('state_startup', sa.Text))
        batch_op.add_column(sa.Column('state_shutdown', sa.Text))
        batch_op.add_column(sa.Column('startup_value', sa.Float))
        batch_op.add_column(sa.Column('shutdown_value', sa.Float))

    op.execute(
        '''
        UPDATE output
        SET startup_value=0
        '''
    )

    op.execute(
        '''
        UPDATE output
        SET shutdown_value=0
        '''
    )

    op.execute(
        '''
        UPDATE output
        SET state_startup=state_at_startup
        '''
    )

    op.execute(
        '''
        UPDATE output
        SET state_shutdown=state_at_shutdown
        '''
    )

    with op.batch_alter_table("output") as batch_op:
        batch_op.drop_column('state_at_startup')
        batch_op.drop_column('state_at_shutdown')


def downgrade():
    with op.batch_alter_table("output") as batch_op:
        batch_op.drop_column('state_startup')
        batch_op.drop_column('state_shutdown')
        batch_op.drop_column('startup_value')
        batch_op.drop_column('shutdown_value')

    with op.batch_alter_table("output") as batch_op:
        batch_op.add_column(sa.Column('state_at_startup', sa.Boolean))
        batch_op.add_column(sa.Column('state_at_shutdown', sa.Boolean))
