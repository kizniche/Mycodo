"""Add custom_options to function tables

Revision ID: 706a32b64ba2
Revises: 313a6fb99082
Create Date: 2020-12-22 15:11:42.441917

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '706a32b64ba2'
down_revision = '313a6fb99082'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("conditional") as batch_op:
        batch_op.add_column(sa.Column('custom_options', sa.Text))

    op.execute(
        '''
        UPDATE conditional
        SET custom_options=''
        '''
    )


def downgrade():
    with op.batch_alter_table("conditional") as batch_op:
        batch_op.drop_column('custom_options')
