"""Add use_pylint option to conditional

Revision ID: 16b28ef31b5b
Revises: 16f4749215ac
Create Date: 2022-12-20 17:35:41.432756

"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))

from alembic_db.alembic_post_utils import write_revision_post_alembic

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '16b28ef31b5b'
down_revision = '16f4749215ac'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("conditional") as batch_op:
        batch_op.add_column(sa.Column('use_pylint', sa.Boolean))

    op.execute(
        '''
        UPDATE conditional
        SET use_pylint=1
        '''
    )


def downgrade():
    with op.batch_alter_table("conditional") as batch_op:
        batch_op.drop_column('use_pylint')
