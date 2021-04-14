"""Add camera option fps

Revision ID: 211cd8cc576b
Revises: d342e17c6e8d
Create Date: 2021-04-09 17:58:09.639426

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '211cd8cc576b'
down_revision = 'd342e17c6e8d'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("camera") as batch_op:
        batch_op.add_column(sa.Column('stream_fps', sa.Integer))

    op.execute(
        '''
        UPDATE camera
        SET stream_fps=5
        '''
    )


def downgrade():
    with op.batch_alter_table("camera") as batch_op:
        batch_op.drop_column('stream_fps')
