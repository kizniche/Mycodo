"""Refactor python execution systems

Revision ID: 65271370a3a9
Revises: 6333b0832b3d
Create Date: 2019-07-26 10:31:39.953722

"""
import sys

import os

sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))

from databases.alembic_post import write_revision_post_alembic


# revision identifiers, used by Alembic.
revision = '65271370a3a9'
down_revision = '6333b0832b3d'
branch_labels = None
depends_on = None


def upgrade():
    write_revision_post_alembic(revision)


def downgrade():
    pass
