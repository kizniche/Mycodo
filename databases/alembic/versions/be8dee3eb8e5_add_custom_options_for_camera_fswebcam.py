"""Add custom_options for camera fswebcam

Revision ID: be8dee3eb8e5
Revises: ba31c9ef6eab
Create Date: 2018-03-07 16:10:41.263785

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'be8dee3eb8e5'
down_revision = 'ba31c9ef6eab'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("camera") as batch_op:
        batch_op.add_column(sa.Column('custom_options', sa.Text))

    op.execute(
        '''
        UPDATE camera
        SET custom_options=''
        '''
    )


def downgrade():
    with op.batch_alter_table("camera") as batch_op:
        batch_op.drop_column('custom_options')
