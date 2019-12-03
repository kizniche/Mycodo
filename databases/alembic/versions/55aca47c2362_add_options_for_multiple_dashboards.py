"""Add options for multiple dashboards

Revision ID: 55aca47c2362
Revises: c1cb0775f7ce
Create Date: 2019-12-02 18:34:28.985810

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '55aca47c2362'
down_revision = 'c1cb0775f7ce'
branch_labels = None
depends_on = None


def upgrade():
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))
    from databases.alembic_post_utils import write_revision_post_alembic
    write_revision_post_alembic(revision)

    op.create_table(
        'dashboard_layout',
        sa.Column('id', sa.Integer, nullable=False, unique=True),
        sa.Column('unique_id', sa.String, nullable=False, unique=True),
        sa.Column('name', sa.Text),
        sa.PrimaryKeyConstraint('id'),
        keep_existing=True)

    with op.batch_alter_table("dashboard") as batch_op:
        batch_op.add_column(sa.Column('dashboard_id', sa.String))


def downgrade():
    op.drop_table('dashboard_layout')

    with op.batch_alter_table("dashboard") as batch_op:
        batch_op.drop_column('dashboard_id')
