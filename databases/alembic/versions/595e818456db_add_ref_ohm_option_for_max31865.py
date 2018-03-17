"""Add ref_ohm option for MAX31865

Revision ID: 595e818456db
Revises: fdb54958dd73
Create Date: 2018-03-17 12:26:26.103144

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '595e818456db'
down_revision = 'fdb54958dd73'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("sensor") as batch_op:
        batch_op.add_column(sa.Column('ref_ohm', sa.Integer))


def downgrade():
    with op.batch_alter_table("sensor") as batch_op:
        batch_op.drop_column('ref_ohm')
