"""Add widget options

Revision ID: c1cb0775f7ce
Revises: 7f4c173f644d
Create Date: 2019-11-27 08:40:48.570802

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c1cb0775f7ce'
down_revision = '7f4c173f644d'
branch_labels = None
depends_on = None


def upgrade():
    # import sys
    # import os
    # sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))
    # from databases.alembic_post_utils import write_revision_post_alembic
    # write_revision_post_alembic(revision)

    with op.batch_alter_table("dashboard") as batch_op:
        batch_op.add_column(sa.Column('enable_drag_handle', sa.Boolean))
        batch_op.add_column(sa.Column('enable_header_buttons', sa.Boolean))
        batch_op.add_column(sa.Column('font_em_name', sa.Float))

    with op.batch_alter_table("misc") as batch_op:
        batch_op.add_column(sa.Column('grid_cell_height', sa.Integer))

    op.execute(
        '''
        UPDATE dashboard
        SET enable_drag_handle=1
        '''
    )

    op.execute(
        '''
        UPDATE dashboard
        SET enable_header_buttons=1
        '''
    )

    op.execute(
        '''
        UPDATE dashboard
        SET font_em_name=1
        '''
    )

    op.execute(
        '''
        UPDATE misc
        SET grid_cell_height=60
        '''
    )


def downgrade():
    with op.batch_alter_table("dashboard") as batch_op:
        batch_op.drop_column('enable_drag_handle')
        batch_op.drop_column('enable_header_buttons')
        batch_op.drop_column('font_em_name')

    with op.batch_alter_table("misc") as batch_op:
        batch_op.drop_column('grid_cell_height')
