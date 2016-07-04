"""Rename Timers table to Timer

Revision ID: 5d5a7158bfe2
Revises: 5e92903dfd13
Create Date: 2016-04-21 19:13:47.285534

"""

# revision identifiers, used by Alembic.
revision = '5d5a7158bfe2'
down_revision = '5e92903dfd13'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.rename_table('timers', 'timer')


def downgrade():
    op.rename_table('timer', 'timers')
