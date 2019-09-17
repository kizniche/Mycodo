"""Update Conditional Statements for new functionality

Revision ID: 70c828e05255
Revises: 0797d251d77d
Create Date: 2019-01-18 19:11:51.806582

"""
import sys

import os

sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))

from mycodo.scripts.alembic_post import write_revision_post_alembic


# revision identifiers, used by Alembic.
revision = '70c828e05255'
down_revision = '0797d251d77d'
branch_labels = None
depends_on = None


def upgrade():
    write_revision_post_alembic(revision)


def downgrade():
    pass
