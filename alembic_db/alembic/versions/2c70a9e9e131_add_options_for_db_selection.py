"""add options for db selection

Revision ID: 2c70a9e9e131
Revises: 743de2cd05e3
Create Date: 2022-05-28 10:24:26.553274

"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))

from alembic_db.alembic_post_utils import write_revision_post_alembic

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2c70a9e9e131'
down_revision = '743de2cd05e3'
branch_labels = None
depends_on = None


def upgrade():
    # write_revision_post_alembic(revision)

    with op.batch_alter_table("misc") as batch_op:
        batch_op.add_column(sa.Column('measurement_db_name', sa.Text))
        batch_op.add_column(sa.Column('measurement_db_version', sa.Text))
        batch_op.add_column(sa.Column('measurement_db_host', sa.Text))
        batch_op.add_column(sa.Column('measurement_db_port', sa.Integer))
        batch_op.add_column(sa.Column('measurement_db_user', sa.Text))
        batch_op.add_column(sa.Column('measurement_db_password', sa.Text))
        batch_op.add_column(sa.Column('measurement_db_dbname', sa.Text))

    op.execute(
        '''
        UPDATE misc
        SET measurement_db_name='influxdb'
        '''
    )

    op.execute(
        '''
        UPDATE misc
        SET measurement_db_version='1'
        '''
    )

    op.execute(
        '''
        UPDATE misc
        SET measurement_db_host='localhost'
        '''
    )

    op.execute(
        '''
        UPDATE misc
        SET measurement_db_port=8086
        '''
    )

    op.execute(
        '''
        UPDATE misc
        SET measurement_db_user='mycodo'
        '''
    )

    op.execute(
        '''
        UPDATE misc
        SET measurement_db_password='mmdu77sj3nIoiajjs'
        '''
    )

    op.execute(
        '''
        UPDATE misc
        SET measurement_db_dbname='mycodo_db'
        '''
    )


def downgrade():
    with op.batch_alter_table("misc") as batch_op:
        batch_op.drop_column('measurement_db_name')
        batch_op.drop_column('measurement_db_version')
        batch_op.drop_column('measurement_db_host')
        batch_op.drop_column('measurement_db_port')
        batch_op.drop_column('measurement_db_user')
        batch_op.drop_column('measurement_db_password')
        batch_op.drop_column('measurement_db_dbname')
