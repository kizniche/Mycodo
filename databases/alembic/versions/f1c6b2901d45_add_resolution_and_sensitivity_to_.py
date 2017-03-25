"""Add resolution and sensitivity to sensor table (for BH1750 sensor)

Revision ID: f1c6b2901d45
Revises: 059a47f950b8
Create Date: 2017-03-25 19:20:02.867211

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1c6b2901d45'
down_revision = '059a47f950b8'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("sensor") as batch_op:
        batch_op.add_column(sa.Column('resolution', sa.INTEGER))
        batch_op.add_column(sa.Column('sensitivity', sa.INTEGER))


def downgrade():
    with op.batch_alter_table("sensor") as batch_op:
        batch_op.drop_column('resolution')
        batch_op.drop_column('sensitivity')
