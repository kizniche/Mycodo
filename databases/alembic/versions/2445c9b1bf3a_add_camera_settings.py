"""Add camera settings

Revision ID: 2445c9b1bf3a
Revises: 054aacc97ae8
Create Date: 2016-09-17 17:49:09.618827

"""

# revision identifiers, used by Alembic.
revision = '2445c9b1bf3a'
down_revision = '054aacc97ae8'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("camerastill") as batch_op:
        batch_op.add_column(sa.Column('hflip', sa.BOOLEAN))
        batch_op.add_column(sa.Column('vflip', sa.BOOLEAN))
        batch_op.add_column(sa.Column('rotation', sa.INT))

    op.execute(
      sa.table('camerastill', sa.column('hflip')).update().values(hflip='0'))
    op.execute(
      sa.table('camerastill', sa.column('vflip')).update().values(vflip='0'))
    op.execute(
      sa.table('camerastill', sa.column('rotation')).update().values(rotation='0'))

    with op.batch_alter_table("pid") as batch_op:
        batch_op.add_column(sa.Column('integrator_min', sa.REAL))
        batch_op.add_column(sa.Column('integrator_max', sa.REAL))

    op.execute(
        '''
        UPDATE pid
        SET integrator_min='-500'
        WHERE integrator_min IS NULL
        '''
    )
    op.execute(
        '''
        UPDATE pid
        SET integrator_max='500'
        WHERE integrator_max IS NULL
        '''
    )


def downgrade():
    with op.batch_alter_table("camerastill") as batch_op:
        batch_op.drop_column('hflip')
        batch_op.drop_column('vflip')
        batch_op.drop_column('rotation')

    with op.batch_alter_table("pid") as batch_op:
        batch_op.drop_column('integrator_min')
        batch_op.drop_column('integrator_max')
