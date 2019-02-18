"""change LCD 16x4 to 20x4

Revision ID: 2976b41930ad
Revises: a8341ac0d779
Create Date: 2019-02-17 18:25:31.478802

"""
from alembic import op
import sqlalchemy as sa


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

    with op.batch_alter_table("output") as batch_op:
        batch_op.add_column(sa.Column('state_at_startup', sa.Boolean))
        batch_op.add_column(sa.Column('state_at_shutdown', sa.Boolean))
        batch_op.add_column(sa.Column('on_state', sa.Boolean))

    op.execute(
        '''
        UPDATE output
        SET on_state=NULL
        '''
    )

    op.execute(
        '''
        UPDATE output
        SET on_state=0
        WHERE trigger=0
        '''
    )

    op.execute(
        '''
        UPDATE output
        SET on_state=1
        WHERE trigger=1
        '''
    )

    op.execute(
        '''
        UPDATE output
        SET state_at_startup=1
        WHERE on_at_start=1
        '''
    )

    op.execute(
        '''
        UPDATE output
        SET state_at_startup=0
        WHERE on_at_start=0
        '''
    )

    op.execute(
        '''
        UPDATE output
        SET state_at_shutdown=0
        '''
    )

    with op.batch_alter_table("output") as batch_op:
        batch_op.drop_column('on_at_start')
        batch_op.drop_column('trigger')


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

    with op.batch_alter_table("output") as batch_op:
        batch_op.add_column(sa.Column('on_at_start', sa.Boolean))
        batch_op.add_column(sa.Column('trigger', sa.Boolean))

    op.execute(
        '''
        UPDATE output
        SET trigger=0
        WHERE on_state=0
        '''
    )

    op.execute(
        '''
        UPDATE output
        SET trigger=1
        WHERE on_state=1
        '''
    )

    op.execute(
        '''
        UPDATE output
        SET on_at_start=1
        WHERE state_at_startup=1
        '''
    )

    op.execute(
        '''
        UPDATE output
        SET on_at_start=0
        WHERE state_at_startup=0
        '''
    )

    with op.batch_alter_table("output") as batch_op:
        batch_op.drop_column('state_at_startup')
        batch_op.drop_column('state_at_shutdown')
        batch_op.drop_column('on_state')
