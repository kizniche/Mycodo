"""Add password reset capabilities

Revision ID: 61a0d0568d24
Revises: f5b77ef5f17c
Create Date: 2020-05-02 19:42:57.036054

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '61a0d0568d24'
down_revision = 'f5b77ef5f17c'
branch_labels = None
depends_on = None


def upgrade():
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))
    from databases.alembic_post_utils import write_revision_post_alembic
    write_revision_post_alembic(revision)

    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column('password_reset_code', sa.Text))
        batch_op.add_column(sa.Column('password_reset_code_expiration', sa.DateTime))
        batch_op.add_column(sa.Column('password_reset_last_request', sa.DateTime))

    with op.batch_alter_table("roles") as batch_op:
        batch_op.add_column(sa.Column('reset_password', sa.Boolean, nullable=False, default=False))


def downgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column('password_reset_code')
        batch_op.drop_column('password_reset_code_expiration')
        batch_op.drop_column('password_reset_last_request')

    with op.batch_alter_table("roles") as batch_op:
        batch_op.drop_column('reset_password')
