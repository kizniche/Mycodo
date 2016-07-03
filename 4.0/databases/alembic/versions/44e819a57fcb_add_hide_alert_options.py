"""Add hide alert options

Revision ID: 44e819a57fcb
Revises: 04303bc223c4
Create Date: 2016-05-02 22:35:21.925523

"""

# revision identifiers, used by Alembic.
revision = '44e819a57fcb'
down_revision = '04303bc223c4'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("misc") as batch_op:
        batch_op.add_column(sa.Column('hide_alert_success', sa.BOOLEAN))
        batch_op.add_column(sa.Column('hide_alert_info', sa.BOOLEAN))
        batch_op.add_column(sa.Column('hide_alert_warning', sa.BOOLEAN))

def downgrade():
    with op.batch_alter_table("misc") as batch_op:
        batch_op.drop_column('hide_alert_success')
        batch_op.drop_column('hide_alert_info')
        batch_op.drop_column('hide_alert_warning')
