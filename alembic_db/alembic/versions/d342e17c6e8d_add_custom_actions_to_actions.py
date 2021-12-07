"""Add custom_actions to Actions

Revision ID: d342e17c6e8d
Revises: 110d2d00e91d
Create Date: 2021-04-07 16:25:50.058409

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd342e17c6e8d'
down_revision = '110d2d00e91d'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("function_actions") as batch_op:
        batch_op.add_column(sa.Column('custom_options', sa.String))

    op.execute(
        '''
        UPDATE function_actions
        SET custom_options='{}'
        '''
    )


def downgrade():
    with op.batch_alter_table("function_actions") as batch_op:
        batch_op.drop_column('custom_options')
