# coding=utf-8
from flask_babel import lazy_gettext

from mycodo.config import SQL_DATABASE_MYCODO
from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import Actions
from mycodo.databases.models import Camera
from mycodo.databases.utils import session_scope
from mycodo.function_actions.base_function_action import AbstractFunctionAction
from mycodo.utils.database import db_retrieve_table_daemon

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO

FUNCTION_ACTION_INFORMATION = {
    'name_unique': 'camera_timelapse_pause',
    'name': '{}: {}: {}'.format(
        TRANSLATIONS['camera']['title'], TRANSLATIONS['timelapse']['title'], TRANSLATIONS['pause']['title']),
    'library': None,
    'manufacturer': 'Mycodo',

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': 'Pause a camera time-lapse',

    'usage': 'Executing <strong>self.run_action("{ACTION_ID}")</strong> will pause the selected Camera time-lapse. '
             'Executing <strong>self.run_action("{ACTION_ID}", value="959019d1-c1fa-41fe-a554-7be3366a9c5b")</strong> will pause the Camera time-lapse with the specified ID (e.g. 959019d1-c1fa-41fe-a554-7be3366a9c5b).',

    'dependencies_module': [],

    'custom_options': [
        {
            'id': 'controller',
            'type': 'select_device',
            'default_value': '',
            'options_select': [
                'Camera'
            ],
            'name': lazy_gettext('Camera'),
            'phrase': 'Select the Camera to pause the time-lapse'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """
    Function Action: Camera Time-lapse Pause
    """
    def __init__(self, action_dev, testing=False):
        super(ActionModule, self).__init__(action_dev, testing=testing, name=__name__)

        self.controller_id = None

        action = db_retrieve_table_daemon(
            Actions, unique_id=self.unique_id)
        self.setup_custom_options(
            FUNCTION_ACTION_INFORMATION['custom_options'], action)

        if not testing:
            self.setup_action()

    def setup_action(self):
        self.action_setup = True

    def run_action(self, message, dict_vars):
        values_set = False
        if "value" in dict_vars and dict_vars["value"] is not None:
            try:
                controller_id = dict_vars["value"]
                values_set = True
            except:
                self.logger.exception("Error setting values passed to action")

        if not values_set:
            controller_id = self.controller_id

        if not controller_id:
            msg = " Controller not selected."
            message += msg
            self.logger.error(msg)
            return message

        this_camera = db_retrieve_table_daemon(
            Camera, unique_id=controller_id, entry='first')

        if not this_camera:
            msg = " Camera not found."
            message += msg
            self.logger.error(msg)
            return message

        message += " Pause timelapse with Camera {unique_id} ({id}, {name}).".format(
            unique_id=controller_id,
            id=this_camera.id,
            name=this_camera.name)
        with session_scope(MYCODO_DB_PATH) as new_session:
            mod_camera = new_session.query(Camera).filter(
                Camera.unique_id == controller_id).first()
            mod_camera.timelapse_paused = True
            new_session.commit()

        return message

    def is_setup(self):
        return self.action_setup
