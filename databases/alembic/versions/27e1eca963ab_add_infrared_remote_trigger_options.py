"""Add infrared remote Trigger options

Revision ID: 27e1eca963ab
Revises: 2976b41930ad
Create Date: 2019-02-21 18:32:44.850304

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '27e1eca963ab'
down_revision = '2976b41930ad'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("trigger") as batch_op:
        batch_op.add_column(sa.Column('program', sa.Text))
        batch_op.add_column(sa.Column('word', sa.Text))


def downgrade():
    with op.batch_alter_table("trigger") as batch_op:
        batch_op.drop_column('program')
        batch_op.drop_column('word')
