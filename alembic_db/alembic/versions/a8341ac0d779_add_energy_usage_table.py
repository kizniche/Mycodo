"""Add energy_usage table

Revision ID: a8341ac0d779
Revises: ed21c36670f4
Create Date: 2019-02-03 13:30:00.941576

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a8341ac0d779'
down_revision = 'ed21c36670f4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'energy_usage',
        sa.Column('id', sa.Integer, nullable=False, unique=True),
        sa.Column('unique_id', sa.String, nullable=False, unique=True),
        sa.Column('name', sa.Text),
        sa.Column('device_id', sa.Text),
        sa.Column('measurement_id', sa.Text),
        sa.PrimaryKeyConstraint('id'),
        keep_existing=True)


def downgrade():
    op.drop_table('energy_usage')
