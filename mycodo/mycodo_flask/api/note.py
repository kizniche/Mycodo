# coding=utf-8
import logging
import traceback

import flask_login
from flask_accept import accept
from flask_restx import Resource, abort, fields

from mycodo.databases.models import NoteTags
from mycodo.databases.models import Notes
from mycodo.mycodo_flask.api import api, default_responses
from mycodo.mycodo_flask.utils import utils_general

logger = logging.getLogger(__name__)

ns_note = api.namespace(
    'notes', description='Note operations')

note_create_fields = ns_note.model('Note Creation Fields', {
    'tags': fields.String(
        description='List of tag names, separated by commas',
        required=True,
        example='tag1,tag2,tag3'),
    'name': fields.String(
        description='The note name.',
        required=True,
        example='Note Name'),
    'note': fields.String(
        description='The note text.',
        required=True,
        example='My Note.')
})


@ns_note.route('/create')
@ns_note.doc(
    security='apikey',
    responses=default_responses
)
class MeasurementsCreate(Resource):
    """Interacts with Notes in the SQL database."""

    @accept('application/vnd.mycodo.v1+json')
    @ns_note.expect(note_create_fields)
    @flask_login.login_required
    def post(self):
        """Create a note."""
        if not utils_general.user_has_permission('edit_controllers'):
            abort(403)

        tags = None
        name = None
        note = None

        if ns_note.payload:
            if 'tags' in ns_note.payload:
                tags = ns_note.payload["tags"]
                if tags is not None:
                    try:
                        tags = tags.split(",")
                    except Exception:
                        abort(422, message='tags must represent comma separated tags')

            if 'name' in ns_note.payload:
                name = ns_note.payload["name"]
                if name is not None:
                    try:
                        name = str(name)
                    except Exception:
                        abort(422, message='name must represent a string')

            if 'note' in ns_note.payload:
                note = ns_note.payload["note"]
                if note is not None:
                    try:
                        note = str(note)
                    except Exception:
                        abort(422, message='note must represent a string')

        try:
            error = []
            list_tags = []

            new_note = Notes()

            for each_tag in tags:
                check_tag = NoteTags.query.filter(
                    NoteTags.unique_id == each_tag).first()
                if not check_tag:
                    error.append("Invalid tag: {}".format(each_tag))
                else:
                    list_tags.append(check_tag.unique_id)
            new_note.tags = ",".join(list_tags)

            if not error:
                new_note.name = name
                new_note.note = note
                new_note.save()
            else:
                abort(500,
                      message=f'Errors: {", ".join(error)}')

            return {'message': 'Success'}, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())
