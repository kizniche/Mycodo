"""Add PID setpoint_tracking and copy method ID

Revision ID: 895ddcdef4ce
Revises: 0ce53d526f13
Create Date: 2019-10-02 16:15:59.230612

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '895ddcdef4ce'
down_revision = '0ce53d526f13'
branch_labels = None
depends_on = None


def upgrade():
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))
    from databases.alembic_post_utils import write_revision_post_alembic
    write_revision_post_alembic(revision)

    with op.batch_alter_table("pid") as batch_op:
        batch_op.add_column(sa.Column('setpoint_tracking_type', sa.Text))
        batch_op.add_column(sa.Column('setpoint_tracking_id', sa.Text))
        batch_op.add_column(sa.Column('setpoint_tracking_max_age', sa.Float))

    op.execute(
        '''
        UPDATE pid
        SET setpoint_tracking_id=method_id
        '''
    )

    with op.batch_alter_table("pid") as batch_op:
        batch_op.drop_column('method_id')


def downgrade():
    with op.batch_alter_table("pid") as batch_op:
        batch_op.drop_column('setpoint_tracking_type')
        batch_op.drop_column('setpoint_tracking_id')
        batch_op.drop_column('setpoint_tracking_max_age')

    with op.batch_alter_table("pid") as batch_op:
        batch_op.add_column(sa.Column('method_id', sa.Text))
