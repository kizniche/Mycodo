"""Add Refractory Period option for Conditionals

Revision ID: 01ba9473fc96
Revises: 595e818456db
Create Date: 2018-03-20 14:40:06.723094

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '01ba9473fc96'
down_revision = '595e818456db'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("conditional") as batch_op:
        batch_op.add_column(sa.Column('if_sensor_refractory_period', sa.Float))

    op.execute(
        '''
        UPDATE conditional
        SET if_sensor_refractory_period=0
        '''
    )


def downgrade():
    with op.batch_alter_table("conditional") as batch_op:
        batch_op.drop_column('if_sensor_refractory_period')
