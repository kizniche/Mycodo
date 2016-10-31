# coding=utf-8
""" A collection of model factories using factory boy """
import factory
from mycodo.databases.users_db import models


class UserFactory(factory.Factory):
    """ A factory for creating user models """
    class Meta(object):
        model = models.Users

    user_name = factory.Faker('name')
    user_email = factory.Faker('email')


# Another, different, factory for the same object
class AdminFactory(factory.Factory):
    """ A factory for creating admin user models """
    class Meta(object):
        model = models.Users

    user_name = factory.Faker('admin_name')
    user_email = factory.Faker('admin_email')
    user_restriction = "admin"


# Guest factory
class GuestFactory(factory.Factory):
    """ A factory for creating admin user models """
    class Meta(object):
        model = models.Users

    user_name = factory.Faker('guest_name')
    user_email = factory.Faker('guest_email')
    user_restriction = "guest"
