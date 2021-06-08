"""add login code

Revision ID: 490e89f108b3
Revises: 43c72773dbe8
Create Date: 2021-06-08 11:02:18.276933

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '490e89f108b3'
down_revision = '43c72773dbe8'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column('code', sa.Integer))

    with op.batch_alter_table("misc") as batch_op:
        batch_op.add_column(sa.Column('default_login_page', sa.String))

    op.execute(
        '''
        UPDATE misc
        SET default_login_page='password'
        '''
    )


def downgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column('code')

    with op.batch_alter_table("misc") as batch_op:
        batch_op.drop_column('default_login_page')
