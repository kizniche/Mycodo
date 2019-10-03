# coding=utf-8
#
# controller_pocketsphinx.py - Pocketsphinx controller for speech recognition
#
#  Copyright (C) 2017  Kyle T. Gabriel
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
import threading
import time
import timeit

from flask_babel import lazy_gettext

from mycodo.controllers.base_controller import AbstractController
from mycodo.databases.models import CustomController
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.database import db_retrieve_table_daemon


def constraints_pass_positive_value(mod_controller, value):
    """
    Check if the user controller is acceptable
    :param mod_controller: SQL object with user-saved Input options
    :param value: float or int
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure value is positive
    if value <= 0:
        all_passed = False
        errors.append("Must be a positive value")
    return all_passed, errors, mod_controller


CONTROLLER_INFORMATION = {
    'controller_name_unique': 'POCKETSPHINX',
    'controller_name': 'Pocketsphinx Speech Recognition',

    'options_enabled': [
        'custom_options'
    ],

    'dependencies_module': [
        ('pip-pypi', 'pocketsphinx', 'pocketsphinx')
    ],

    'custom_options': [
        {
            'id': 'text_1',
            'type': 'text',
            'default_value': 'Text_1',
            'required': True,
            'name': lazy_gettext('Text 1'),
            'phrase': lazy_gettext('Text 1 Description')
        },
        {
            'id': 'integer_1',
            'type': 'integer',
            'default_value': 100,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': lazy_gettext('Integer 1'),
            'phrase': lazy_gettext('Integer 1 Description')
        },
        {
            'id': 'bool_1',
            'type': 'bool',
            'default_value': True,
            'name': lazy_gettext('Boolean 1'),
            'phrase': lazy_gettext('Boolean 1 Description')
        },
    ]
}


class CustomModule(AbstractController, threading.Thread):
    """
    Class to operate Pocketsphinx controller
    """
    def __init__(self, ready, unique_id, testing=False):
        threading.Thread.__init__(self)
        super(CustomModule, self).__init__(ready, unique_id=unique_id, name=__name__)

        self.unique_id = unique_id
        self.log_level_debug = None

        self.control = DaemonControl()

        # Initialize custom options
        self.text_1 = None
        self.integer_1 = None
        self.bool_1 = None
        # Set custom options
        custom_controller = db_retrieve_table_daemon(
            CustomController, unique_id=unique_id)
        self.setup_custom_options(
            CONTROLLER_INFORMATION['custom_options'], custom_controller)

        if not testing:
            # from pocketsphinx import LiveSpeech
            # self.livespeech = LiveSpeech
            pass

    def run(self):
        try:
            self.logger.info("Activated in {:.1f} ms".format(
                (timeit.default_timer() - self.thread_startup_timer) * 1000))

            self.ready.set()
            self.running = True

            self.logger.debug("Pocketsphinx starting: {}, {}, {}...".format(
                self.text_1, self.integer_1, self.bool_1))

            while self.running:
                time.sleep(1)
            # for phrase in self.livespeech():
            #     self.logger.debug(phrase)
        except:
            self.logger.exception("Run Error")
        finally:
            self.run_finally()
            self.running = False
            if self.thread_shutdown_timer:
                self.logger.info("Deactivated in {:.1f} ms".format(
                    (timeit.default_timer() - self.thread_shutdown_timer) * 1000))
            else:
                self.logger.error("Deactivated unexpectedly")

    def loop(self):
        pass

    def initialize_variables(self):
        controller = db_retrieve_table_daemon(
            CustomController, unique_id=self.unique_id)
        self.log_level_debug = controller.log_level_debug
