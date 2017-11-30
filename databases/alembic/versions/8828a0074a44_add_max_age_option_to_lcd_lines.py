"""Add Max Age option to LCD lines

Revision ID: 8828a0074a44
Revises: 3dcf34dd7caf
Create Date: 2017-11-21 16:21:19.184946

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8828a0074a44'
down_revision = '3dcf34dd7caf'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("lcd_data") as batch_op:
        batch_op.add_column(sa.Column('line_1_max_age', sa.Integer))
        batch_op.add_column(sa.Column('line_2_max_age', sa.Integer))
        batch_op.add_column(sa.Column('line_3_max_age', sa.Integer))
        batch_op.add_column(sa.Column('line_4_max_age', sa.Integer))

    op.execute(
        '''
        UPDATE lcd_data
        SET line_1_max_age=360
        '''
    )

    op.execute(
        '''
        UPDATE lcd_data
        SET line_2_max_age=360
        '''
    )

    op.execute(
        '''
        UPDATE lcd_data
        SET line_3_max_age=360
        '''
    )

    op.execute(
        '''
        UPDATE lcd_data
        SET line_4_max_age=360
        '''
    )


def downgrade():
    with op.batch_alter_table("lcd_data") as batch_op:
        batch_op.drop_column('line_1_max_age')
        batch_op.drop_column('line_2_max_age')
        batch_op.drop_column('line_3_max_age')
        batch_op.drop_column('line_4_max_age')
