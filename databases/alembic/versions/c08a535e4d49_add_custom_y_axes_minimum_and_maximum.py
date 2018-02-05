"""Add custom y-axes minimum and maximum

Revision ID: c08a535e4d49
Revises: 69e9443c319f
Create Date: 2018-02-05 17:18:07.800938

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c08a535e4d49'
down_revision = '69e9443c319f'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("graph") as batch_op:
        batch_op.add_column(sa.Column('custom_yaxes', sa.Text))

    op.execute(
        '''
        UPDATE graph
        SET custom_yaxes=''
        '''
    )


def downgrade():
    with op.batch_alter_table("graph") as batch_op:
        batch_op.drop_column('custom_yaxes')
