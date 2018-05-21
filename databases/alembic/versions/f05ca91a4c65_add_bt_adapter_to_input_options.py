"""Add bt_adapter to input options

Revision ID: f05ca91a4c65
Revises: b2c19049035f
Create Date: 2018-05-21 16:47:14.135883

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f05ca91a4c65'
down_revision = 'b2c19049035f'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("input") as batch_op:
        batch_op.add_column(sa.Column('bt_adapter', sa.Text))

    op.execute(
        '''
        UPDATE input
        SET bt_adapter='hci0'
        '''
    )


def downgrade():
    with op.batch_alter_table("input") as batch_op:
        batch_op.drop_column('bt_adapter')