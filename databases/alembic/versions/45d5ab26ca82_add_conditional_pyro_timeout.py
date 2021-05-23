"""add conditional pyro_timeout

Revision ID: 45d5ab26ca82
Revises: d46e17d65f48
Create Date: 2021-05-23 17:32:08.997850

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '45d5ab26ca82'
down_revision = 'd46e17d65f48'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("conditional") as batch_op:
        batch_op.add_column(sa.Column('pyro_timeout', sa.Float))

    op.execute(
        '''
        UPDATE conditional
        SET pyro_timeout=30
        '''
    )


def downgrade():
    with op.batch_alter_table("conditional") as batch_op:
        batch_op.drop_column('pyro_timeout')
