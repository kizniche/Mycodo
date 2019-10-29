"""Add IP and port options for internet check

Revision ID: f4bd467eb5fe
Revises: 8f9bf3fe5ec2
Create Date: 2019-10-29 14:13:24.755398

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f4bd467eb5fe'
down_revision = '8f9bf3fe5ec2'
branch_labels = None
depends_on = None


def upgrade():
    # import sys
    # import os
    # sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))
    # from databases.alembic_post_utils import write_revision_post_alembic
    # write_revision_post_alembic(revision)

    with op.batch_alter_table("misc") as batch_op:
        batch_op.add_column(sa.Column('net_test_ip', sa.String))
        batch_op.add_column(sa.Column('net_test_port', sa.Integer))
        batch_op.add_column(sa.Column('net_test_timeout', sa.Integer))

    op.execute(
        '''
        UPDATE misc
        SET net_test_ip='8.8.8.8'
        '''
    )

    op.execute(
        '''
        UPDATE misc
        SET net_test_port=53
        '''
    )

    op.execute(
        '''
        UPDATE misc
        SET net_test_timeout=3
        '''
    )


def downgrade():
    with op.batch_alter_table("misc") as batch_op:
        batch_op.drop_column('net_test_ip')
        batch_op.drop_column('net_test_port')
        batch_op.drop_column('net_test_timeout')
