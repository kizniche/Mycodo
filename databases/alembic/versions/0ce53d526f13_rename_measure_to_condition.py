"""rename measure() to condition()

Revision ID: 0ce53d526f13
Revises: 9f6bc3a1a450
Create Date: 2019-09-22 19:44:44.105105

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0ce53d526f13'
down_revision = '9f6bc3a1a450'
branch_labels = None
depends_on = None


def upgrade():
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))
    from databases.alembic_post_utils import write_revision_post_alembic
    write_revision_post_alembic(revision)


def downgrade():
    pass
