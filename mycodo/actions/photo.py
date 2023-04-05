# coding=utf-8
from flask_babel import lazy_gettext

from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import Actions
from mycodo.databases.models import Camera
from mycodo.devices.camera import camera_record
from mycodo.actions.base_action import AbstractFunctionAction
from mycodo.utils.database import db_retrieve_table_daemon

ACTION_INFORMATION = {
    'name_unique': 'photo',
    'name': "{}: {}".format(TRANSLATIONS['camera']['title'], lazy_gettext('Capture Photo')),
    'library': None,
    'manufacturer': 'Mycodo',
    'application': ['functions'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': lazy_gettext('Capture a photo with the selected Camera.'),

    'usage': 'Executing <strong>self.run_action("ACTION_ID")</strong> will capture a photo with the selected Camera. '
             'Executing <strong>self.run_action("ACTION_ID", value={"camera_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b"})</strong> will capture a photo with the Camera with the specified ID. Don\'t forget to change the camera_id value to an actual Camera ID that exists in your system.',

    'custom_options': [
        {
            'id': 'controller',
            'type': 'select_device',
            'default_value': '',
            'options_select': [
                'Camera'
            ],
            'name': lazy_gettext('Camera'),
            'phrase': 'Select the Camera to take a photo'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """Function Action: Capture Photo."""
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

        camera = db_retrieve_table_daemon(
            Camera, unique_id=controller_id, entry='first')

        if not camera:
            msg = f" Error: Camera with ID '{controller_id}' not found."
            dict_vars['message'] += msg
            self.logger.error(msg)
            return dict_vars

        dict_vars['message'] += f" Capturing photo with camera {controller_id} ({camera.name})."

        path, filename = camera_record('photo', controller_id)
        if not path and not filename:
            msg = " Could not acquire image."
            self.logger.error(msg)
            dict_vars['message'] += msg

        self.logger.debug(f"Message: {dict_vars['message']}")

        return dict_vars

    def is_setup(self):
        return self.action_setup
