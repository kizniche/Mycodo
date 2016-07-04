"""Add edge detection to sensor conditionals

Revision ID: d549de374d71
Revises: 7a3ae1ec200d
Create Date: 2016-06-29 20:32:19.739291

"""

# revision identifiers, used by Alembic.
revision = 'd549de374d71'
down_revision = '7a3ae1ec200d'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("sensorconditional") as batch_op:
        batch_op.add_column(sa.Column('edge_detected', sa.TEXT))


def downgrade():
    with op.batch_alter_table("sensorconditional") as batch_op:
        batch_op.drop_column('edge_detected')
