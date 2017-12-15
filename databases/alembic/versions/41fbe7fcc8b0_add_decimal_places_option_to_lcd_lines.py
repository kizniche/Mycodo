"""Add decimal places option to LCD lines

Revision ID: 41fbe7fcc8b0
Revises: d36de7e4e477
Create Date: 2017-12-14 21:47:29.603232

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '41fbe7fcc8b0'
down_revision = 'd36de7e4e477'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("lcd_data") as batch_op:
        batch_op.add_column(sa.Column('line_1_decimal_places', sa.INTEGER))
        batch_op.add_column(sa.Column('line_2_decimal_places', sa.INTEGER))
        batch_op.add_column(sa.Column('line_3_decimal_places', sa.INTEGER))
        batch_op.add_column(sa.Column('line_4_decimal_places', sa.INTEGER))

    op.execute(
        '''
        UPDATE lcd_data
        SET line_1_decimal_places=2
        WHERE line_1_decimal_places IS NULL
        '''
    )

    op.execute(
        '''
        UPDATE lcd_data
        SET line_2_decimal_places=2
        WHERE line_2_decimal_places IS NULL
        '''
    )

    op.execute(
        '''
        UPDATE lcd_data
        SET line_3_decimal_places=2
        WHERE line_3_decimal_places IS NULL
        '''
    )

    op.execute(
        '''
        UPDATE lcd_data
        SET line_4_decimal_places=2
        WHERE line_4_decimal_places IS NULL
        '''
    )



def downgrade():
    with op.batch_alter_table("lcd_data") as batch_op:
        batch_op.drop_column('line_1_decimal_places')
        batch_op.drop_column('line_2_decimal_places')
        batch_op.drop_column('line_3_decimal_places')
        batch_op.drop_column('line_4_decimal_places')
