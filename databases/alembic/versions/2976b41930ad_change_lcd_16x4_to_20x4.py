"""change LCD 16x4 to 20x4

Revision ID: 2976b41930ad
Revises: a8341ac0d779
Create Date: 2019-02-17 18:25:31.478802

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '2976b41930ad'
down_revision = 'a8341ac0d779'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        '''
        UPDATE lcd
        SET x_characters=20
        WHERE lcd_type='16x4_generic'
        '''
    )

    op.execute(
        '''
        UPDATE lcd
        SET lcd_type='20x4_generic'
        WHERE lcd_type='16x4_generic'
        '''
    )


def downgrade():
    op.execute(
        '''
        UPDATE lcd
        SET x_characters=16
        WHERE lcd_type='20x4_generic'
        '''
    )

    op.execute(
        '''
        UPDATE lcd
        SET lcd_type='16x4_generic'
        WHERE lcd_type='20x4_generic'
        '''
    )
