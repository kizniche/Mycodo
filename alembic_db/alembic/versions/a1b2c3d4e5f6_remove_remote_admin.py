"""Remove remote admin table and remote_host display-order column

Revision ID: a1b2c3d4e5f6
Revises: 9bdb60d2a2cd
Create Date: 2026-04-16 00:00:00.000000

Removes:
  - The ``remote`` table (stored remote-host credentials including bcrypt
    password hashes that were transmitted over the wire — a security risk).
  - The ``remote_host`` column from the ``displayorder`` table.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '9bdb60d2a2cd'
branch_labels = None
depends_on = None


def upgrade():
    # Remove the remote_host ordering column from displayorder
    with op.batch_alter_table("displayorder") as batch_op:
        batch_op.drop_column('remote_host')

    # Drop the remote table entirely
    op.drop_table('remote')


def downgrade():
    # Recreate the remote table
    op.create_table(
        'remote',
        sa.Column('id', sa.Integer, primary_key=True, unique=True),
        sa.Column('unique_id', sa.String(36), nullable=False, unique=True),
        sa.Column('is_activated', sa.Boolean, default=False),
        sa.Column('host', sa.Text, default=''),
        sa.Column('username', sa.Text, default=''),
        sa.Column('password_hash', sa.Text, default=''),
    )

    # Restore the remote_host column on displayorder
    with op.batch_alter_table("displayorder") as batch_op:
        batch_op.add_column(sa.Column('remote_host', sa.Text, default=''))

