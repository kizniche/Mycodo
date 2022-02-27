"""update user for Command Function Actions

Revision ID: 313a6fb99082
Revises: 03331fc158bc
Create Date: 2020-12-19 18:24:58.481151

"""
# revision identifiers, used by Alembic.
revision = '313a6fb99082'
down_revision = '03331fc158bc'
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
