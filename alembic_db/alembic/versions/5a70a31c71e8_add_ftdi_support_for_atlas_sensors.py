"""Add FTDI support for Atlas sensors

Revision ID: 5a70a31c71e8
Revises: b4d958997cf0
Create Date: 2019-01-07 21:29:23.714062

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5a70a31c71e8'
down_revision = 'b4d958997cf0'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("input") as batch_op:
        batch_op.add_column(sa.Column('ftdi_location', sa.Text))


def downgrade():
    with op.batch_alter_table("input") as batch_op:
        batch_op.drop_column('ftdi_location')
