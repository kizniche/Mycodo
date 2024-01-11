"""add hostname override setting

Revision ID: c7942284b74e
Revises: 16b28ef31b5b
Create Date: 2024-01-11 17:51:39.799272

"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))

from alembic_db.alembic_post_utils import write_revision_post_alembic

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c7942284b74e'
down_revision = '16b28ef31b5b'
branch_labels = None
depends_on = None


def upgrade():
    write_revision_post_alembic(revision)

    with op.batch_alter_table("misc") as batch_op:
        batch_op.add_column(sa.Column('hostname_override', sa.Boolean))

    op.execute(
        '''
        UPDATE misc
        SET hostname_override=""
        '''
    )


def downgrade():
    with op.batch_alter_table("misc") as batch_op:
        batch_op.drop_column('hostname_override')