"""Ensure Pyro5 is installed

Revision ID: 802cc65f734e
Revises: 96ac315ec212
Create Date: 2019-09-18 11:07:04.814951

"""

# revision identifiers, used by Alembic.
revision = '802cc65f734e'
down_revision = '96ac315ec212'
branch_labels = None
depends_on = None


def upgrade():
    # No database schema changes, just need to execute post-alembic code
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))
    from databases.alembic_post import write_revision_post_alembic
    write_revision_post_alembic(revision)


def downgrade():
    pass
