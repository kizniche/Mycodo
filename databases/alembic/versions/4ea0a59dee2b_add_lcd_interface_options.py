"""Add LCD interface options

Revision ID: 4ea0a59dee2b
Revises: af5891792291
Create Date: 2020-07-20 02:02:12.215884

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4ea0a59dee2b'
down_revision = 'af5891792291'
branch_labels = None
depends_on = None


def upgrade():
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))
    from databases.alembic_post_utils import write_revision_post_alembic
    write_revision_post_alembic(revision)

    with op.batch_alter_table("lcd") as batch_op:
        batch_op.add_column(sa.Column('interface', sa.String))
        batch_op.add_column(sa.Column('pin_dc', sa.Integer))
        batch_op.add_column(sa.Column('spi_device', sa.Integer))
        batch_op.add_column(sa.Column('spi_bus', sa.Integer))

def downgrade():
    with op.batch_alter_table("lcd") as batch_op:
        batch_op.drop_column('interface')
        batch_op.drop_column('pin_dc')
        batch_op.drop_column('spi_device')
        batch_op.drop_column('spi_bus')
