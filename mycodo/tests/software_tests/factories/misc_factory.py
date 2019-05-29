# coding=utf-8
""" A collection of model factories using factory boy """
import factory  # factory boy
from mycodo.mycodo_flask.extensions import db
from mycodo.databases import models
from faker import Faker


faker = Faker()


class MiscFactory(factory.alchemy.SQLAlchemyModelFactory):
    """ A factory for creating user models """
    class Meta(object):
        model = models.Misc
        sqlalchemy_session = db.session
