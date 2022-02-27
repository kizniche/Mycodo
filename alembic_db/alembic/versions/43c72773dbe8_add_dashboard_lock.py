"""Add dashboard lock

Revision ID: 43c72773dbe8
Revises: 45d5ab26ca82
Create Date: 2021-05-26 09:28:08.590158

"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '43c72773dbe8'
down_revision = '45d5ab26ca82'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("dashboard") as batch_op:
        batch_op.add_column(sa.Column('locked', sa.Boolean))

    op.execute(
        '''
        UPDATE dashboard
        SET locked=0
        '''
    )


def downgrade():
    with op.batch_alter_table("dashboard") as batch_op:
        batch_op.drop_column('locked')
