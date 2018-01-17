"""Add ability to manually set graph y-axis min/max

Revision ID: 15f825bca2f5
Revises: 4bb64e530d87
Create Date: 2018-01-17 11:37:32.588764

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '15f825bca2f5'
down_revision = '4bb64e530d87'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("graph") as batch_op:
        batch_op.add_column(sa.Column('enable_manual_y_axis', sa.Boolean))

    op.execute(
        '''
        UPDATE graph
        SET enable_manual_y_axis=0
        '''
    )

def downgrade():
    with op.batch_alter_table("graph") as batch_op:
        batch_op.drop_column('enable_manual_y_axis')
