"""rename dashboard table

Revision ID: 69960a0722a7
Revises: 55aca47c2362
Create Date: 2019-12-04 20:38:29.859998

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '69960a0722a7'
down_revision = '55aca47c2362'
branch_labels = None
depends_on = None


def upgrade():
    # import sys
    # import os
    # sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))
    # from alembic.alembic_post_utils import write_revision_post_alembic
    # write_revision_post_alembic(revision)

    op.rename_table('dashboard', 'widget')
    op.rename_table('dashboard_layout', 'dashboard')


def downgrade():
    op.rename_table('widget', 'dashboard')
    op.rename_table('dashboard', 'dashboard_layout')
