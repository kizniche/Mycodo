"""add favicon options

Revision ID: 5966b3569c89
Revises: 435f35958689
Create Date: 2024-10-01 13:39:25.265702

"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))

from alembic_db.alembic_post_utils import write_revision_post_alembic

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5966b3569c89'
down_revision = '435f35958689'
branch_labels = None
depends_on = None


def upgrade():
    # write_revision_post_alembic(revision)

    with op.batch_alter_table("misc") as batch_op:
        batch_op.add_column(sa.Column('favicon_display', sa.Text))
        batch_op.add_column(sa.Column('brand_favicon', sa.BLOB))

    op.execute(
        '''
        UPDATE misc
        SET favicon_display='default'
        '''
    )


def downgrade():
    with op.batch_alter_table("misc") as batch_op:
        batch_op.drop_column('favicon_display')
        batch_op.drop_column('brand_favicon')
