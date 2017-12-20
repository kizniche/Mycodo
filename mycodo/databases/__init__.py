# coding=utf-8
import uuid

from flask import current_app

from mycodo.mycodo_flask.extensions import db


class CRUDMixin(object):
    """
    Basic Create, Read, Update and Delete methods
    Models that inherit from this class automatically get these CRUD methods
    """

    def save(self):
        """ creates the model in the database """
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except Exception as error:
            db.session.rollback()
            current_app.logger.error("Failed to save {model} due to error: {err}".format(model=self, err=error))

    def delete(self):
        """ deletes the record from the database """
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as error:
            current_app.logger.error("Failed to delete '{record}': '{err}'".format(record=self, err=error))


def set_uuid():
    """ returns a uuid string """
    return str(uuid.uuid4())