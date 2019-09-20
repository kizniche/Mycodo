"""Add line_text to lcd table and delete line_type

Revision ID: 9f6bc3a1a450
Revises: 545744b31813
Create Date: 2019-09-20 14:25:08.190223

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9f6bc3a1a450'
down_revision = '545744b31813'
branch_labels = None
depends_on = None


def upgrade():
    # import sys
    # import os
    # sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))
    # from databases.alembic_post import write_revision_post_alembic
    # write_revision_post_alembic(revision)

    with op.batch_alter_table("lcd_data") as batch_op:
        batch_op.add_column(sa.Column('line_1_text', sa.Text))
        batch_op.add_column(sa.Column('line_2_text', sa.Text))
        batch_op.add_column(sa.Column('line_3_text', sa.Text))
        batch_op.add_column(sa.Column('line_4_text', sa.Text))
        batch_op.add_column(sa.Column('line_5_text', sa.Text))
        batch_op.add_column(sa.Column('line_6_text', sa.Text))
        batch_op.add_column(sa.Column('line_7_text', sa.Text))
        batch_op.add_column(sa.Column('line_8_text', sa.Text))
        batch_op.drop_column('line_1_type')
        batch_op.drop_column('line_2_type')
        batch_op.drop_column('line_3_type')
        batch_op.drop_column('line_4_type')
        batch_op.drop_column('line_5_type')
        batch_op.drop_column('line_6_type')
        batch_op.drop_column('line_7_type')
        batch_op.drop_column('line_8_type')


def downgrade():
    with op.batch_alter_table("lcd_data") as batch_op:
        batch_op.add_column(sa.Column('line_1_type', sa.Text))
        batch_op.add_column(sa.Column('line_2_type', sa.Text))
        batch_op.add_column(sa.Column('line_3_type', sa.Text))
        batch_op.add_column(sa.Column('line_4_type', sa.Text))
        batch_op.add_column(sa.Column('line_5_type', sa.Text))
        batch_op.add_column(sa.Column('line_6_type', sa.Text))
        batch_op.add_column(sa.Column('line_7_type', sa.Text))
        batch_op.add_column(sa.Column('line_8_type', sa.Text))
        batch_op.drop_column('line_1_text')
        batch_op.drop_column('line_2_text')
        batch_op.drop_column('line_3_text')
        batch_op.drop_column('line_4_text')
        batch_op.drop_column('line_5_text')
        batch_op.drop_column('line_6_text')
        batch_op.drop_column('line_7_text')
        batch_op.drop_column('line_8_text')
