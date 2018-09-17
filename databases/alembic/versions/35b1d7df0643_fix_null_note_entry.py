"""Fix null note entry

Revision ID: 35b1d7df0643
Revises: d10573676ecb
Create Date: 2018-09-17 12:19:24.193007

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '35b1d7df0643'
down_revision = 'd10573676ecb'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        '''
        UPDATE dashboard
        SET note_tag_ids=''
        WHERE note_tag_ids IS NULL
        '''
    )


def downgrade():
    pass
