"""add Inputs Server Ping and Server Port Open

Revision ID: b7acb4de5e00
Revises: 15f825bca2f5
Create Date: 2018-01-21 18:58:18.823215

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7acb4de5e00'
down_revision = '15f825bca2f5'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("sensor") as batch_op:
        batch_op.add_column(sa.Column('port', sa.Integer))
        batch_op.add_column(sa.Column('times_check', sa.Integer))
        batch_op.add_column(sa.Column('deadline', sa.Integer))


def downgrade():
    with op.batch_alter_table("sensor") as batch_op:
        batch_op.drop_column('port')
        batch_op.drop_column('times_check')
        batch_op.drop_column('deadline')
