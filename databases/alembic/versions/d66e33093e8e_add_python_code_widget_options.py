"""add Python Code widget options

Revision ID: d66e33093e8e
Revises: 4d3258ef5864
Create Date: 2020-07-30 10:04:55.625878

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd66e33093e8e'
down_revision = '4d3258ef5864'
branch_labels = None
depends_on = None


def upgrade():
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))
    from databases.alembic_post_utils import write_revision_post_alembic
    write_revision_post_alembic(revision)

    with op.batch_alter_table("widget") as batch_op:
        batch_op.add_column(sa.Column('period', sa.Float))
        batch_op.add_column(sa.Column('custom_options', sa.String))
        batch_op.add_column(sa.Column('log_level_debug', sa.Boolean))

    with op.batch_alter_table("misc") as batch_op:
        batch_op.add_column(sa.Column('sample_rate_controller_widget', sa.Float))

    op.execute(
        '''
        UPDATE widget
        SET period=30
        '''
    )

    op.execute(
        '''
        UPDATE widget
        SET custom_options=''
        '''
    )

    op.execute(
        '''
        UPDATE widget
        SET log_level_debug=0
        '''
    )

    op.execute(
        '''
        UPDATE misc
        SET sample_rate_controller_widget=0.25
        '''
    )


def downgrade():
    with op.batch_alter_table("widget") as batch_op:
        batch_op.drop_column('period')
        batch_op.drop_column('custom_options')
        batch_op.drop_column('log_level_debug')

    with op.batch_alter_table("misc") as batch_op:
        batch_op.drop_column('sample_rate_controller_widget')
