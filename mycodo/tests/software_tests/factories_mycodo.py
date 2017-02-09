# coding=utf-8
""" A collection of model factories using factory boy """
import factory
from mycodo.databases.mycodo_db import models_5


class SensorFactory(factory.Factory):
    """ A factory for creating sensor models """
    class Meta(object):
        model = models_5.Sensor

    id = ''
    name = ''
