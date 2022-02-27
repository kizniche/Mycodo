# coding=utf-8
from flask_babel import lazy_gettext

from mycodo.config import SQL_DATABASE_MYCODO
from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import Actions
from mycodo.databases.models import NoteTags
from mycodo.databases.models import Notes
from mycodo.databases.utils import session_scope
from mycodo.function_actions.base_function_action import AbstractFunctionAction
from mycodo.utils.database import db_retrieve_table_daemon

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO

FUNCTION_ACTION_INFORMATION = {
    'name_unique': 'create_note',
    'name': '{}: {}'.format(TRANSLATIONS['create']['title'], TRANSLATIONS['note']['title']),
    'message': lazy_gettext('Create a note with the selected Tag.'),
    'library': None,
    'manufacturer': 'Mycodo',

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'usage': 'Executing <strong>self.run_action("{ACTION_ID}")</strong> will create a note with the selected tag and note. '
             'Executing <strong>self.run_action("{ACTION_ID}", value=["tag1,tag2", "note"])</strong> will create a note with the tag(s) (multiple separated by commas) and note (e.g. tags "tag1,tag2" and note "note"). If note is not specified, then the action message is saved as the note (e.g. value=["tag1", ""])',

    'dependencies_module': [],

    'custom_options': [
        {
            'id': 'tag',
            'type': 'select_multi_measurement',
            'default_value': '',
            'options_select': [
                'Tag'
            ],
            'name': lazy_gettext('Note Tags'),
            'phrase': 'Select one or more tags'
        },
        {
            'id': 'note',
            'type': 'text',
            'default_value': '',
            'required': False,
            'name': 'Note',
            'phrase': 'The body of the note'
        },
    ]
}


class ActionModule(AbstractFunctionAction):
    """
    Function Action: Create Note
    """
    def __init__(self, action_dev, testing=False):
        super(ActionModule, self).__init__(action_dev, testing=testing, name=__name__)

        self.tag = None
        self.note = None

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
        list_tags = []
        if "value" in dict_vars and len(dict_vars["value"]) == 2:
            try:
                tag = dict_vars["value"][0]
                if "," in tag:
                    list_tags = tag.split(',')
                else:
                    list_tags = [tag]
                note = dict_vars["value"][1]
                values_set = True
            except:
                self.logger.exception("Error setting values passed to action")

        if not values_set:
            list_tags = []
            for each_id_set in self.tag:
                list_tags.append(each_id_set.split(",")[0])
            note = self.note

        with session_scope(MYCODO_DB_PATH) as new_session:
            list_tag_names = []
            for each_tag in list_tags:
                # First check name
                tag_check = new_session.query(NoteTags).filter(NoteTags.name == each_tag).first()
                if tag_check:
                    list_tag_names.append(tag_check.name)
                else:
                    # Next check ID
                    tag_check = new_session.query(NoteTags).filter(NoteTags.unique_id == each_tag).first()
                    if tag_check:
                        list_tag_names.append(tag_check.name)
                    else:
                        self.logger.error("Tag with name or id '{}' does not exist.".format(each_tag))

            if not list_tag_names:
                msg = "No valid tags specified. Cannot create note."
                message += msg
                self.logger.error(msg)
                return message

            message += " Create note with tag(s) '{}'".format(','.join(list_tag_names))
            if note:
                message += " and note {}".format(note)
            message += "."

            new_note = Notes()
            new_note.name = 'Action'
            new_note.tags = ','.join(list_tag_names)
            if note:
                new_note.note = note
            else:
                new_note.note = message
            new_session.add(new_note)

        return message

    def is_setup(self):
        return self.action_setup
