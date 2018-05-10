"""add camera output duration

Revision ID: b2c19049035f
Revises: 0a29a4ab7273
Create Date: 2018-05-08 16:37:48.049063

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2c19049035f'
down_revision = '0a29a4ab7273'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("camera") as batch_op:
        batch_op.add_column(sa.Column('output_duration', sa.Float))

    with op.batch_alter_table("input") as batch_op:
        batch_op.add_column(sa.Column('resolution_2', sa.Integer))

    op.execute(
        '''
        UPDATE camera
        SET output_duration=3.0
        '''
    )


def downgrade():
    with op.batch_alter_table("camera") as batch_op:
        batch_op.drop_column('output_duration')

    with op.batch_alter_table("input") as batch_op:
        batch_op.drop_column('resolution_2')
