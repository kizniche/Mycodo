"""Add general controller conditional action

Revision ID: 758f88901bbc
Revises: d881bacc5814
Create Date: 2018-04-08 16:22:19.709465

"""
import sys
import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.orm import Session

sys.path.insert(0, '/var/mycodo-root')

from mycodo.databases.models import Conditional
from mycodo.databases.models import ConditionalActions
from mycodo.databases.models import Dashboard
from mycodo.databases.models import LCD
from mycodo.databases.models import LCDData
from mycodo.databases.models import Method
from mycodo.databases.models import MethodData
from mycodo.databases.models import Role
from mycodo.databases.models import Timer
from mycodo.databases.models import User

# revision identifiers, used by Alembic.
revision = '758f88901bbc'
down_revision = 'd881bacc5814'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("timer") as batch_op:
        batch_op.add_column(sa.Column('unique_id', sa.Text))

    with op.batch_alter_table("lcd") as batch_op:
        batch_op.add_column(sa.Column('unique_id', sa.Text))

    with op.batch_alter_table("lcd_data") as batch_op:
        batch_op.add_column(sa.Column('unique_id', sa.Text))

    with op.batch_alter_table("graph") as batch_op:
        batch_op.add_column(sa.Column('unique_id', sa.Text))

    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column('unique_id', sa.Text))

    with op.batch_alter_table("roles") as batch_op:
        batch_op.add_column(sa.Column('unique_id', sa.Text))

    with op.batch_alter_table("method") as batch_op:
        batch_op.add_column(sa.Column('unique_id', sa.Text))

    with op.batch_alter_table("method_data") as batch_op:
        batch_op.add_column(sa.Column('unique_id', sa.Text))

    with op.batch_alter_table("conditional") as batch_op:
        batch_op.add_column(sa.Column('unique_id', sa.Text))

    with op.batch_alter_table("conditional_data") as batch_op:
        batch_op.add_column(sa.Column('unique_id', sa.Text))
        batch_op.add_column(sa.Column('do_unique_id', sa.Text))

    conn = op.get_bind()
    session = Session(bind=conn)

    for item in session.query(Conditional).filter_by(unique_id=None):
        item.unique_id = str(uuid.uuid4())

    for item in session.query(ConditionalActions).filter_by(unique_id=None):
        item.unique_id = str(uuid.uuid4())

    for item in session.query(Dashboard).filter_by(unique_id=None):
        item.unique_id = str(uuid.uuid4())

    for item in session.query(LCD).filter_by(unique_id=None):
        item.unique_id = str(uuid.uuid4())

    for item in session.query(LCDData).filter_by(unique_id=None):
        item.unique_id = str(uuid.uuid4())

    for item in session.query(Method).filter_by(unique_id=None):
        item.unique_id = str(uuid.uuid4())

    for item in session.query(MethodData).filter_by(unique_id=None):
        item.unique_id = str(uuid.uuid4())

    for item in session.query(User).filter_by(unique_id=None):
        item.unique_id = str(uuid.uuid4())

    for item in session.query(Role).filter_by(unique_id=None):
        item.unique_id = str(uuid.uuid4())

    for item in session.query(LCDData).filter_by(unique_id=None):
        item.unique_id = str(uuid.uuid4())

    for item in session.query(Timer).filter_by(unique_id=None):
        item.unique_id = str(uuid.uuid4())

    session.commit()


def downgrade():
    with op.batch_alter_table("conditional_data") as batch_op:
        batch_op.drop_column('do_unique_id')
