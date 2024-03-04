"""add custom CSS

Revision ID: a338ed3dce74
Revises: c7942284b74e
Create Date: 2024-03-01 22:46:52.383396

"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))

from alembic_db.alembic_post_utils import write_revision_post_alembic

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a338ed3dce74'
down_revision = 'c7942284b74e'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("misc") as batch_op:
        batch_op.add_column(sa.Column('custom_css', sa.Text))

    op.execute(
        '''
        UPDATE misc
        SET custom_css=''
        '''
    )


def downgrade():
    with op.batch_alter_table("misc") as batch_op:
        batch_op.drop_column('custom_css')
