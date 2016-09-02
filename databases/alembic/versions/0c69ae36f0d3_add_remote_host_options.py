"""Add remote host options

Revision ID: 0c69ae36f0d3
Revises: efa3afc7d152
Create Date: 2016-06-12 18:27:46.857729

"""

# revision identifiers, used by Alembic.
revision = '0c69ae36f0d3'
down_revision = 'efa3afc7d152'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'remote',
        sa.Column('id', sa.TEXT,  unique=True, primary_key=True),
        sa.Column('activated', sa.INT),
        sa.Column('host', sa.TEXT),
        sa.Column('username', sa.TEXT),
        sa.Column('password_hash', sa.TEXT)
    )
    with op.batch_alter_table("displayorder") as batch_op:
        batch_op.add_column(sa.Column('remote_host', sa.TEXT))
    op.execute(
        '''
        UPDATE displayorder
        SET remote_host=''
        WHERE remote_host IS NULL
        '''
    )

def downgrade():
    op.drop_table('remote')
    with op.batch_alter_table("displayorder") as batch_op:
        batch_op.drop_column('remote_host')
