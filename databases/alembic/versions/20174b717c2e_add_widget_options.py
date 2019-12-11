"""add widget options

Revision ID: 20174b717c2e
Revises: 69960a0722a7
Create Date: 2019-12-10 20:58:48.381181

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20174b717c2e'
down_revision = '69960a0722a7'
branch_labels = None
depends_on = None


def upgrade():
    # import sys
    # import os
    # sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))
    # from databases.alembic_post_utils import write_revision_post_alembic
    # write_revision_post_alembic(revision)

    with op.batch_alter_table("widget") as batch_op:
        batch_op.add_column(sa.Column('enable_status', sa.Boolean))
        batch_op.add_column(sa.Column('enable_value', sa.Boolean))
        batch_op.add_column(sa.Column('enable_name', sa.Boolean))
        batch_op.add_column(sa.Column('enable_unit', sa.Boolean))
        batch_op.add_column(sa.Column('enable_measurement', sa.Boolean))
        batch_op.add_column(sa.Column('enable_channel', sa.Boolean))

    op.execute(
        '''
        UPDATE widget
        SET enable_status=1
        '''
    )

    op.execute(
        '''
        UPDATE widget
        SET enable_value=1
        '''
    )

    op.execute(
        '''
        UPDATE widget
        SET enable_name=1
        '''
    )

    op.execute(
        '''
        UPDATE widget
        SET enable_unit=1
        '''
    )

    op.execute(
        '''
        UPDATE widget
        SET enable_measurement=1
        '''
    )

    op.execute(
        '''
        UPDATE widget
        SET enable_channel=1
        '''
    )


def downgrade():
    with op.batch_alter_table("widget") as batch_op:
        batch_op.drop_column('enable_status')
        batch_op.drop_column('enable_name')
        batch_op.drop_column('enable_unit')
        batch_op.drop_column('enable_measurement')
        batch_op.drop_column('enable_channel')
