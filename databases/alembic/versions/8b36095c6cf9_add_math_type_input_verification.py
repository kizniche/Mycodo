"""Add Math type: Input Verification

Revision ID: 8b36095c6cf9
Revises: b9712d4ec64e
Create Date: 2017-12-06 21:50:59.112331

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8b36095c6cf9'
down_revision = 'b9712d4ec64e'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("math") as batch_op:
        batch_op.add_column(sa.Column('max_difference', sa.FLOAT))
        batch_op.add_column(sa.Column('dry_bulb_t_id', sa.FLOAT))
        batch_op.add_column(sa.Column('dry_bulb_t_measure', sa.FLOAT))
        batch_op.add_column(sa.Column('wet_bulb_t_id', sa.FLOAT))
        batch_op.add_column(sa.Column('wet_bulb_t_measure', sa.FLOAT))
        batch_op.add_column(sa.Column('pressure_pa_id', sa.FLOAT))
        batch_op.add_column(sa.Column('pressure_pa_measure', sa.FLOAT))


def downgrade():
    with op.batch_alter_table("math") as batch_op:
        batch_op.drop_column('max_difference')
        batch_op.drop_column('dry_bulb_t_id')
        batch_op.drop_column('dry_bulb_t_measure')
        batch_op.drop_column('wet_bulb_t_id')
        batch_op.drop_column('wet_bulb_t_measure')
        batch_op.drop_column('pressure_pa_id')
        batch_op.drop_column('pressure_pa_measure')
