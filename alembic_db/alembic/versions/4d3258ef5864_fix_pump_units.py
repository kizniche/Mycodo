"""Fix pump units

Revision ID: 4d3258ef5864
Revises: 4ea0a59dee2b
Create Date: 2020-07-25 19:30:42.214733

"""

# revision identifiers, used by Alembic.
revision = '4d3258ef5864'
down_revision = '4ea0a59dee2b'
branch_labels = None
depends_on = None


def upgrade():
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))
    from alembic_db.alembic_post_utils import write_revision_post_alembic
    write_revision_post_alembic(revision)


def downgrade():
    pass
