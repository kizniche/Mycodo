# coding=utf-8
""" A collection of model factories using factory boy """
import factory
from mycodo.databases.mycodo_db import models


class UserFactory(factory.Factory):
    """ A factory for creating user models """
    class Meta(object):
        model = models.User

    name = factory.Faker('name')
    email = factory.Faker('email')


# Another, different, factory for the same object
class AdminFactory(factory.Factory):
    """ A factory for creating admin user models """
    class Meta(object):
        model = models.User

    name = factory.Faker('name')
    email = factory.Faker('email')
    role = 1  # Admin


# Guest factory
class GuestFactory(factory.Factory):
    """ A factory for creating admin user models """
    class Meta(object):
        model = models.User

    name = factory.Faker('name')
    email = factory.Faker('email')
    role = 4  # Guest
