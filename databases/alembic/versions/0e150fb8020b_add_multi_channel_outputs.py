"""add multi-channel outputs

Revision ID: 0e150fb8020b
Revises: d66e33093e8e
Create Date: 2020-08-14 20:12:34.650801

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0e150fb8020b'
down_revision = 'd66e33093e8e'
branch_labels = None
depends_on = None


def upgrade():
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))
    from databases.alembic_post_utils import write_revision_post_alembic
    write_revision_post_alembic(revision)

    op.create_table(
        'output_channel',
        sa.Column('id', sa.Integer, nullable=False, unique=True),
        sa.Column('unique_id', sa.String, nullable=False, unique=True),
        sa.Column('output_id', sa.Text),
        sa.Column('channel', sa.Integer),
        sa.Column('name', sa.Text),
        sa.Column('custom_options', sa.Text),
        sa.PrimaryKeyConstraint('id'),
        keep_existing=True
    )

    with op.batch_alter_table("trigger") as batch_op:
        batch_op.add_column(sa.Column('unique_id_3', sa.String))


def downgrade():
    op.drop_table('output_channel')

    with op.batch_alter_table("trigger") as batch_op:
        batch_op.drop_column('unique_id_3')
