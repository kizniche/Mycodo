"""add camera file tracking fields

Revision ID: 0187ea22dc4b
Revises: 6e394f2e8fec
Create Date: 2021-09-03 12:08:49.777948

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0187ea22dc4b"
down_revision = "6e394f2e8fec"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("camera") as batch_op:
        batch_op.add_column(sa.Column("timelapse_last_file", sa.Text))
        batch_op.add_column(sa.Column("timelapse_last_ts", sa.Float))
        batch_op.add_column(sa.Column("still_last_file", sa.Text))
        batch_op.add_column(sa.Column("still_last_ts", sa.Float))


def downgrade():
    with op.batch_alter_table("camera") as batch_op:
        batch_op.drop_column("timelapse_last_file")
        batch_op.drop_column("timelapse_last_ts")
        batch_op.drop_column("still_last_file")
        batch_op.drop_column("still_last_ts")
