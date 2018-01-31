"""Add options for gauge timestamp

Revision ID: 69e9443c319f
Revises: 532644870ad6
Create Date: 2018-01-31 17:44:55.112168

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '69e9443c319f'
down_revision = '532644870ad6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("graph") as batch_op:
        batch_op.add_column(sa.Column('enable_timestamp', sa.Boolean))

    op.execute(
        '''
        UPDATE graph
        SET enable_timestamp=1
        '''
    )


def downgrade():
    with op.batch_alter_table("graph") as batch_op:
        batch_op.drop_column('enable_timestamp')
