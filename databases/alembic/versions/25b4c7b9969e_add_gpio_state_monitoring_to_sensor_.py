"""Add GPIO state monitoring to sensor Edge conditonal

Revision ID: 25b4c7b9969e
Revises: 3ab66300800b
Create Date: 2016-10-02 10:05:56.765921

"""

# revision identifiers, used by Alembic.
revision = '25b4c7b9969e'
down_revision = '3ab66300800b'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("sensorconditional") as batch_op:
        batch_op.add_column(sa.Column('edge_select', sa.TEXT))
        batch_op.add_column(sa.Column('gpio_state', sa.INT))


def downgrade():
    with op.batch_alter_table("sensorconditional") as batch_op:
        batch_op.drop_column('edge_select')
        batch_op.drop_column('gpio_state')
