"""Add dashboard placement columns

Revision ID: 7f4c173f644d
Revises: f4bd467eb5fe
Create Date: 2019-11-24 10:25:35.866805

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7f4c173f644d'
down_revision = 'f4bd467eb5fe'
branch_labels = None
depends_on = None


def upgrade():
    # import sys
    # import os
    # sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))
    # from databases.alembic_post_utils import write_revision_post_alembic
    # write_revision_post_alembic(revision)

    with op.batch_alter_table("dashboard") as batch_op:
        batch_op.add_column(sa.Column('position_x', sa.Integer))
        batch_op.add_column(sa.Column('position_y', sa.Integer))
        batch_op.add_column(sa.Column('size_x', sa.Integer))
        batch_op.add_column(sa.Column('size_y', sa.Integer))

    op.execute(
        '''
        UPDATE dashboard
        SET position_x=0
        '''
    )

    op.execute(
        '''
        UPDATE dashboard
        SET position_y=0
        '''
    )

    op.execute(
        '''
        UPDATE dashboard
        SET size_x=6
        '''
    )

    op.execute(
        '''
        UPDATE dashboard
        SET size_y=6
        '''
    )


def downgrade():
    with op.batch_alter_table("dashboard") as batch_op:
        batch_op.drop_column('position_x')
        batch_op.drop_column('position_y')
        batch_op.drop_column('size_x')
        batch_op.drop_column('size_y')
