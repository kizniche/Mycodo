"""Add output option trigger_functions_at_start

Revision ID: 0797d251d77d
Revises: 5a70a31c71e8
Create Date: 2019-01-09 15:23:51.419313

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0797d251d77d'
down_revision = '5a70a31c71e8'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("output") as batch_op:
        batch_op.add_column(sa.Column('trigger_functions_at_start', sa.Boolean))

    op.execute(
        '''
        UPDATE output
        SET trigger_functions_at_start=1
        '''
    )


def downgrade():
    with op.batch_alter_table("output") as batch_op:
        batch_op.drop_column('trigger_functions_at_start')
