"""split DS18B20 input module for separate libraries

Revision ID: 0a8a5eb1be4b
Revises: 20174b717c2e
Create Date: 2020-02-17 15:05:06.352414

"""
# revision identifiers, used by Alembic.
revision = '0a8a5eb1be4b'
down_revision = '20174b717c2e'
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
