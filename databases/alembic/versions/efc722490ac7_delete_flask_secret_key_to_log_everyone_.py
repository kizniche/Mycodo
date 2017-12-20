"""Delete flask_secret_key to log everyone out

Revision ID: efc722490ac7
Revises: 41fbe7fcc8b0
Create Date: 2017-12-18 18:45:33.229610

"""
import subprocess

import os
import shutil
from alembic import op

# revision identifiers, used by Alembic.
revision = 'efc722490ac7'
down_revision = '41fbe7fcc8b0'
branch_labels = None
depends_on = None


def upgrade():
    """
    A side effect of performing a Mycodo upgrade that migrates all the code
    form Python 2 to Python 3 is a bug emerges for using a cookie generated
    with Flask running on Python 2, with the new Flask running on Python 3.

    Consequently, all users will see Flask throw an error, rendering the web
    user interface useless and leading the user to believe Mycodo is broken,
    when in fact the issue would be resolved by merely deleting the browser
    cookie.

    Using alembic to delete the flask_secret_key will ensure this only occurs
    once, when the user upgrades to a Mycodo version => 5.5.0.
    :return: None
    """
    # Delete flask_secret_key
    DATABASE_DIRECTORY = os.path.dirname(os.path.realpath(__file__)) + '/../..'
    FLASK_SECRET_KEY_PATH = os.path.join(DATABASE_DIRECTORY, 'flask_secret_key')
    os.remove(FLASK_SECRET_KEY_PATH)

    # Touch mycodo_flask.wsgi to cause the Flask web interface to restart. It
    # already is supposed to restart as a part of the upgrade process. This is
    # just making extra sure it happens.
    INSTALL_DIRECTORY = os.path.dirname(os.path.realpath(__file__)) + '/../../..'
    MYCODO_FLASK_WSGI_PATH = os.path.join(INSTALL_DIRECTORY, 'mycodo_flask.wsgi')
    with open(MYCODO_FLASK_WSGI_PATH, 'a'):
        os.utime(MYCODO_FLASK_WSGI_PATH, None)

    # Disable all timelapses for cameras that use the opencv library
    op.execute(
        '''
        UPDATE camera
        SET timelapse_started=0
        WHERE library='opencv'
        AND timelapse_started=1
        '''
    )

    op.execute(
        '''
        UPDATE camera
        SET timelapse_started=0
        WHERE library='opencv'
        AND timelapse_started=1
        '''
    )

    # Delete Python 2.7 virtualenv
    del_env_path = os.path.join(INSTALL_DIRECTORY, 'env')
    shutil.rmtree(del_env_path)

    # Build the python 3.4 virtualenv
    full_cmd = "/bin/bash {pth}/mycodo/scripts/upgrade_commands.sh " \
               "setup-virtualenv-py3".format(pth=INSTALL_DIRECTORY,)
    cmd = subprocess.Popen(full_cmd, stdout=subprocess.PIPE, shell=True)
    cmd_out, cmd_err = cmd.communicate()
    cmd_status = cmd.wait()
    print(cmd_out)


def downgrade():
    pass
