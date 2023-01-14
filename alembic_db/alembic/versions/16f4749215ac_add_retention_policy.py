"""add retention_policy

Revision ID: 16f4749215ac
Revises: 07c7c8ebc195
Create Date: 2022-11-23 18:44:32.626413

"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))

from alembic_db.alembic_post_utils import write_revision_post_alembic

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '16f4749215ac'
down_revision = '07c7c8ebc195'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("misc") as batch_op:
        batch_op.add_column(sa.Column('measurement_db_retention_policy', sa.Text))
    
    db_retention_policy = ""
    try:
        import sys
        import os

        sys.path.append(os.path.abspath(os.path.join(__file__, "../../..")))

        from mycodo.scripts.measurement_db import get_influxdb_info
        info = get_influxdb_info()
        if info['influxdb_version']:
            if info['influxdb_version'].startswith("1"):
                db_retention_policy = 'autogen'
            if info['influxdb_version'].startswith("2"):
                db_retention_policy = 'infinite'
        
        if db_retention_policy:
            op.execute(
                f'''
                UPDATE misc
                SET measurement_db_retention_policy="{db_retention_policy}"
                '''
            )
    except Exception as err:
        print(f"Error: {err}")


def downgrade():
    with op.batch_alter_table("misc") as batch_op:
        batch_op.drop_column('measurement_db_retention_policy')
