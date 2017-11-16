"""Add unique_id for remote table

Revision ID: d0757b2ecd33
Revises: 3c7c2b12389d
Create Date: 2017-11-15 17:34:44.353476

"""
import uuid
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd0757b2ecd33'
down_revision = '3c7c2b12389d'
branch_labels = None
depends_on = None


def set_uuid():
    """ returns a uuid string """
    return str(uuid.uuid4())


def upgrade():
    with op.batch_alter_table("remote") as batch_op:
        batch_op.add_column(sa.Column('unique_id', sa.String))


def downgrade():
    with op.batch_alter_table("remote") as batch_op:
        batch_op.drop_column('unique_id')
