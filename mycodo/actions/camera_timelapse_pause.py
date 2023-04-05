# coding=utf-8
from flask_babel import lazy_gettext

from mycodo.actions.base_action import AbstractFunctionAction
from mycodo.config import MYCODO_DB_PATH
from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import Actions
from mycodo.databases.models import Camera
from mycodo.databases.utils import session_scope
from mycodo.utils.database import db_retrieve_table_daemon


ACTION_INFORMATION = {
    'name_unique': 'camera_timelapse_pause',
    'name': f"{TRANSLATIONS['camera']['title']}: {TRANSLATIONS['timelapse']['title']}: {TRANSLATIONS['pause']['title']}",
    'library': None,
    'manufacturer': 'Mycodo',
    'application': ['functions'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': 'Pause a camera time-lapse',

    'usage': 'Executing <strong>self.run_action("ACTION_ID")</strong> will pause the selected Camera time-lapse. '
             'Executing <strong>self.run_action("ACTION_ID", value={"camera_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b"})</strong> will pause the Camera time-lapse with the specified ID. Don\'t forget to change the camera_id value to an actual Camera ID that exists in your system.',

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
    """Function Action: Camera Time-lapse Pause."""
    def __init__(self, action_dev, testing=False):
        super().__init__(action_dev, testing=testing, name=__name__)

        self.controller_id = None

        action = db_retrieve_table_daemon(
            Actions, unique_id=self.unique_id)
        self.setup_custom_options(
            ACTION_INFORMATION['custom_options'], action)

        if not testing:
            self.try_initialize()

    def initialize(self):
        self.action_setup = True

    def run_action(self, dict_vars):
        try:
            controller_id = dict_vars["value"]["camera_id"]
        except:
            controller_id = self.controller_id

        this_camera = db_retrieve_table_daemon(
            Camera, unique_id=controller_id, entry='first')

        if not this_camera:
            msg = f" Error: Camera with ID '{controller_id}' not found."
            dict_vars['message'] += msg
            self.logger.error(msg)
            return dict_vars

        dict_vars['message'] += f" Pause timelapse with Camera {controller_id} ({this_camera.name})."
        with session_scope(MYCODO_DB_PATH) as new_session:
            mod_camera = new_session.query(Camera).filter(
                Camera.unique_id == controller_id).first()
            mod_camera.timelapse_paused = True
            new_session.commit()

        self.logger.debug(f"Message: {dict_vars['message']}")

        return dict_vars

    def is_setup(self):
        return self.action_setup
