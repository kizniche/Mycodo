# coding=utf-8
#
#  backup_rsync.py - Periodically perform backup of Mycodo assets to remote system using rsync
#
#  Copyright (C) 2015-2020 Kyle T. Gabriel <mycodo@kylegabriel.com>
#
#  This file is part of Mycodo
#
#  Mycodo is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Mycodo is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Mycodo. If not, see <http://www.gnu.org/licenses/>.
#
#  Contact at kylegabriel.com
#
import datetime
import os
import socket
import time

from flask_babel import lazy_gettext

from mycodo.config import ALEMBIC_VERSION
from mycodo.config import MYCODO_VERSION
from mycodo.config import PATH_CAMERAS
from mycodo.config import PATH_SETTINGS_BACKUP
from mycodo.databases.models import CustomController
from mycodo.functions.base_function import AbstractFunction
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.constraints_pass import constraints_pass_positive_value
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.system_pi import assure_path_exists
from mycodo.utils.system_pi import cmd_output
from mycodo.utils.tools import create_settings_export

try:
    host_name = socket.gethostname().replace(' ', '_')
except:
    host_name = 'MY_HOST_NAME'

FUNCTION_INFORMATION = {
    'function_name_unique': 'BACKUP_REMOTE_RSYNC',
    'function_name': 'Backup to Remote Host (rsync)',

    'options_disabled': [
        'measurements_select',
        'measurements_configure'
    ],

    'message': 'This function will use rsync to back up assets on this system to a remote system. Your remote system needs to have an SSH server running and rsync installed. This system will need to be able to access your remote system via SSH without a password. You can do this by creating an SSH key on this system running Mycodo with "ssh-keygen" (leave the password field empty), then run "ssh-copy-id -i ~/.ssh/id_rsa.pub pi@REMOTE_HOST_IP" to transfer your public SSH key to your remote system (changing pi and REMOTE_HOST_IP to the appropriate user and host of your remote system). You can test if this worked by trying to connect to your remote system with "ssh pi@REMOTE_HOST_IP" and you should log in without being asked for a password.',

    'dependencies_module': [
        ('apt', 'rsync', 'rsync')
    ],

    'custom_options': [
        {
            'id': 'period',
            'type': 'float',
            'default_value': 3600,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': lazy_gettext('Period (seconds)'),
            'phrase': lazy_gettext('The duration (seconds) between measurements or actions')
        },
        {
            'id': 'local_user',
            'type': 'text',
            'default_value': 'pi',
            'required': True,
            'name': 'Local User',
            'phrase': 'The user on this system that will run rsync'
        },
        {
            'id': 'remote_user',
            'type': 'text',
            'default_value': 'pi',
            'required': True,
            'name': 'Remote User',
            'phrase': 'The user to log in to the remote host'
        },
        {
            'id': 'remote_host',
            'type': 'text',
            'default_value': '192.168.0.50',
            'required': True,
            'name': 'Remote Host',
            'phrase': 'The IP or host address to send the backup to'
        },
        {
            'id': 'remote_backup_path',
            'type': 'text',
            'default_value': '/home/pi/backup_mycodo_{}'.format(host_name),
            'required': True,
            'name': 'Remote Backup Path',
            'phrase': 'The path to backup to on the remote host'
        },
        {
            'id': 'rsync_timeout',
            'type': 'integer',
            'default_value': 3600,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Rsync Timeout',
            'phrase': 'How long to allow rsync to complete'
        },
        {
            'id': 'backup_settings',
            'type': 'bool',
            'default_value': True,
            'required': True,
            'name': 'Backup Settings Export File',
            'phrase': 'Create and backup exported settings file'
        },
        {
            'id': 'backup_cameras',
            'type': 'bool',
            'default_value': True,
            'required': True,
            'name': 'Backup Camera Directories',
            'phrase': 'Backup all camera directories'
        },
        {
            'id': 'backup_cameras_remove_source',
            'type': 'bool',
            'default_value': False,
            'required': True,
            'name': 'Remove Source Images',
            'phrase': 'Remove source files after successful transfer of camera images'
        }
    ],

    'custom_actions': [
        {
            'type': 'message',
            'default_value': 'Backup of settings are only created if the Mycodo version or database versions change. This is due to this Function running periodically- if it created a new backup every Period, there would soon be many identical backups. Therefore, if you want to induce the creation of a new settings or camera image backup and sync it to your remote system, use the buttons below.',
        },
        {
            'id': 'create_new_settings_backup',
            'type': 'button',
            'wait_for_return': False,
            'name': 'Create New Settings Backup',
            'phrase': 'Create a new settings backup and backup via rsync'
        },
        {
            'id': 'create_new_camera_backup',
            'type': 'button',
            'wait_for_return': False,
            'name': 'Create New Camera Backup',
            'phrase': 'Create a new camera image backup via rsync'
        }
    ]
}


class CustomModule(AbstractFunction):
    """
    Class to operate custom controller
    """

    def __init__(self, function, testing=False):
        super(CustomModule, self).__init__(function, testing=testing, name=__name__)

        self.is_setup = False
        self.timer_loop = time.time()
        self.control = DaemonControl()

        # Initialize custom options
        self.period = None
        self.local_user = None
        self.remote_user = None
        self.remote_host = None
        self.remote_backup_path = None
        self.rsync_timeout = None
        self.backup_settings = None
        self.backup_cameras = None
        self.backup_cameras_remove_source = None

        # Set custom options
        custom_function = db_retrieve_table_daemon(
            CustomController, unique_id=self.unique_id)
        self.setup_custom_options(
            FUNCTION_INFORMATION['custom_options'], custom_function)

        if not testing:
            self.initialize_variables()

    def initialize_variables(self):
        self.logger.debug(
            "Custom controller started with options: {}, {}, {}, {}".format(
                self.remote_host,
                self.remote_user,
                self.remote_backup_path,
                self.backup_settings))

        if self.remote_host and self.remote_user and self.remote_backup_path:
            self.is_setup = True

    def loop(self):
        if self.timer_loop > time.time():
            return

        while self.timer_loop < time.time():
            self.timer_loop += self.period

        if not self.is_setup:
            self.logger.error("Cannot run: Not all options are set")
            return

        if self.backup_settings:
            filename = 'Mycodo_{mver}_Settings_{aver}_{host}.zip'.format(
                mver=MYCODO_VERSION, aver=ALEMBIC_VERSION,
                host=socket.gethostname().replace(' ', ''))
            self.backup_settings(filename)

        if self.backup_cameras:
            self.backup_camera()

    def backup_settings(self, filename):
        path_save = os.path.join(PATH_SETTINGS_BACKUP, filename)
        assure_path_exists(PATH_SETTINGS_BACKUP)
        if os.path.exists(path_save):
            self.logger.debug(
                "Skipping backup of settings: "
                "File already exists: {}".format(path_save))
        else:
            status, saved_path = create_settings_export(save_path=path_save)
            if not status:
                self.logger.debug("Saved settings file: "
                                  "{}".format(saved_path))
            else:
                self.logger.debug("Could not create settings file: "
                                  "{}".format(saved_path))

        rsync_cmd = "rsync -avz -e ssh {path_local} {user}@{host}:{remote_path}".format(
            path_local=PATH_SETTINGS_BACKUP,
            user=self.remote_user,
            host=self.remote_host,
            remote_path=self.remote_backup_path)
        self.logger.debug("rsync command: {}".format(rsync_cmd))
        cmd_out, cmd_err, cmd_status = cmd_output(
            rsync_cmd, timeout=self.rsync_timeout, user=self.local_user)
        self.logger.debug("rsync returned:\nOut: {}\nError: {}\nStatus: {}".format(
            cmd_out.decode(), cmd_err.decode(), cmd_status))

    def backup_camera(self):
        if self.backup_cameras_remove_source:
            rsync_cmd = "rsync --remove-source-files -avz -e ssh {path_local} {user}@{host}:{remote_path}".format(
                path_local=PATH_CAMERAS,
                user=self.remote_user,
                host=self.remote_host,
                remote_path=self.remote_backup_path)
        else:
            rsync_cmd = "rsync -avz -e ssh {path_local} {user}@{host}:{remote_path}".format(
                path_local=PATH_CAMERAS,
                user=self.remote_user,
                host=self.remote_host,
                remote_path=self.remote_backup_path)

        self.logger.debug("rsync command: {}".format(rsync_cmd))
        cmd_out, cmd_err, cmd_status = cmd_output(
            rsync_cmd, timeout=self.rsync_timeout, user=self.local_user)
        self.logger.debug("rsync returned:\nOut: {}\nError: {}\nStatus: {}".format(
            cmd_out.decode(), cmd_err.decode(), cmd_status))

    def create_new_settings_backup(self, args_dict):
        filename = 'Mycodo_{mver}_Settings_{aver}_{host}_{dt}.zip'.format(
            mver=MYCODO_VERSION, aver=ALEMBIC_VERSION,
            host=socket.gethostname().replace(' ', ''),
            dt=datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        self.backup_settings(filename)

    def create_new_camera_backup(self, args_dict):
        self.backup_camera()
