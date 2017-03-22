"""add option to show/hide tooltips

Revision ID: 059a47f950b8
Revises:
Create Date: 2017-03-21 22:21:18.650731

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '059a47f950b8'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("misc") as batch_op:
        batch_op.add_column(sa.Column('hide_tooltips', sa.BOOLEAN))
    op.execute(
        '''
        UPDATE misc
        SET hide_tooltips=0
        WHERE hide_tooltips IS NULL
        '''
    )


def downgrade():
    with op.batch_alter_table("misc") as batch_op:
        batch_op.drop_column('hide_tooltips')


