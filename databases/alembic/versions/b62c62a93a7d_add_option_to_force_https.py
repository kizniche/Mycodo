"""Add option to force HTTPS

Revision ID: b62c62a93a7d
Revises: 0b8ab36548bd
Create Date: 2016-09-07 17:42:38.050403

"""

# revision identifiers, used by Alembic.
revision = 'b62c62a93a7d'
down_revision = '0b8ab36548bd'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("misc") as batch_op:
        batch_op.add_column(sa.Column('force_https', sa.BOOLEAN))
    op.execute(
        '''
        UPDATE misc
        SET force_https=1
        WHERE force_https IS NULL
        '''
    )


def downgrade():
    with op.batch_alter_table("misc") as batch_op:
        batch_op.drop_column('force_https')
