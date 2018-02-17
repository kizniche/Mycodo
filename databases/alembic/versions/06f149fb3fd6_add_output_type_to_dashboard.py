"""add output type to dashboard

Revision ID: 06f149fb3fd6
Revises: c08a535e4d49
Create Date: 2018-02-16 15:20:01.102605

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '06f149fb3fd6'
down_revision = 'c08a535e4d49'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("graph") as batch_op:
        batch_op.add_column(sa.Column('output_ids', sa.Text))
        batch_op.add_column(sa.Column('font_em_value', sa.Float))
        batch_op.add_column(sa.Column('font_em_timestamp', sa.Float))
        batch_op.add_column(sa.Column('enable_output_controls', sa.Boolean))


def downgrade():
    with op.batch_alter_table("graph") as batch_op:
        batch_op.drop_column('output_ids')
        batch_op.drop_column('font_em_value')
        batch_op.drop_column('font_em_timestamp')
        batch_op.drop_column('enable_output_controls')
