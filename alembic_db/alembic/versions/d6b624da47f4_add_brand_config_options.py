"""Add brand config options

Revision ID: d6b624da47f4
Revises: a338ed3dce74
Create Date: 2024-03-29 20:13:51.807396

"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))

from alembic_db.alembic_post_utils import write_revision_post_alembic

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd6b624da47f4'
down_revision = 'a338ed3dce74'
branch_labels = None
depends_on = None


def upgrade():
    # write_revision_post_alembic(revision)

    with op.batch_alter_table("misc") as batch_op:
        batch_op.add_column(sa.Column('brand_display', sa.Text))
        batch_op.add_column(sa.Column('title_display', sa.Text))
        batch_op.add_column(sa.Column('brand_image', sa.BLOB))
        batch_op.add_column(sa.Column('brand_image_height', sa.Integer))

    op.execute(
        '''
        UPDATE misc
        SET brand_display='hostname'
        '''
    )

    op.execute(
        '''
        UPDATE misc
        SET title_display='hostname'
        '''
    )

    op.execute(
        '''
        UPDATE misc
        SET brand_image_height=55
        '''
    )


def downgrade():
    with op.batch_alter_table("misc") as batch_op:
        batch_op.drop_column('brand_display')
        batch_op.drop_column('title_display')
        batch_op.drop_column('brand_image')
        batch_op.drop_column('brand_image_height')
