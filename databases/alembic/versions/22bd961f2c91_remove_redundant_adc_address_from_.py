"""Remove redundant adc_address from sensor table of mycodoSQL database

Revision ID: 22bd961f2c91
Revises: 4d37a6feead5
Create Date: 2016-07-21 16:27:19.633535

"""

# revision identifiers, used by Alembic.
revision = '22bd961f2c91'
down_revision = '4d37a6feead5'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("sensor") as batch_op:
        batch_op.drop_column('adc_address')

def downgrade():
    with op.batch_alter_table("sensor") as batch_op:
        batch_op.add_column(sa.Column('adc_address', sa.TEXT))
