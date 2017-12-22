"""Add conditional display order

Revision ID: f0e4df767286
Revises: efc722490ac7
Create Date: 2017-12-22 11:21:15.742584

"""
from alembic import op
import sqlalchemy as sa

import sys
sys.path.append("/var/www/mycodo")
from mycodo.databases.models import Conditional
from mycodo.utils.database import db_retrieve_table_daemon

# revision identifiers, used by Alembic.
revision = 'f0e4df767286'
down_revision = 'efc722490ac7'
branch_labels = None
depends_on = None


def create_order_str():
    conditional = db_retrieve_table_daemon(Conditional)
    order_list = []
    for each_conditional in conditional:
        order_list.append(each_conditional.id)
    if order_list:
        order_str = ','.join(map(str, order_list))
        return order_str
    return ''


def upgrade():
    with op.batch_alter_table("displayorder") as batch_op:
        batch_op.add_column(sa.Column('conditional', sa.TEXT))

    with op.batch_alter_table("conditional") as batch_op:
        batch_op.add_column(sa.Column('measurement', sa.TEXT))

    op.execute(
        '''
        UPDATE displayorder
        SET conditional='{}'
        '''.format(create_order_str())
    )

    op.execute(
        '''
        UPDATE conditional
        SET is_activated=0
        '''
    )


def downgrade():
    with op.batch_alter_table("displayorder") as batch_op:
        batch_op.drop_column('conditional')

    with op.batch_alter_table("conditional") as batch_op:
        batch_op.drop_column('measurement')
