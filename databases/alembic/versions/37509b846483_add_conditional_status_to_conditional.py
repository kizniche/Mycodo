"""Add conditional_status to conditional

Revision ID: 37509b846483
Revises: 490e89f108b3
Create Date: 2021-06-13 18:33:32.482443

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '37509b846483'
down_revision = '490e89f108b3'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("conditional") as batch_op:
        batch_op.add_column(sa.Column('conditional_status', sa.Text))

    op.execute(
        '''
        UPDATE conditional
        SET conditional_status=''
        '''
    )


def downgrade():
    with op.batch_alter_table("conditional") as batch_op:
        batch_op.drop_column('conditional_status')
