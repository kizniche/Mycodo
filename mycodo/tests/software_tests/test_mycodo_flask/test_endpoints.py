# coding=utf-8
""" functional tests for flask endpoints """
import pytest
import mock
from mycodo.databases.models import Input
from mycodo.databases.models import User

from mycodo.tests.software_tests.conftest import login_user
from mycodo.tests.software_tests.factories import UserFactory


# ----------------------
#   Non-Logged In Tests
# ----------------------
def redirects_to_login_page(testapp, endpoint):
    """ helper function that verifies that we see the login page """
    response = testapp.get(endpoint, expect_errors=True).maybe_follow()
    assert response.status_code == 200, "Response Status Failure: {}".format(endpoint)
    assert "Mycodo Login" in response


def redirects_to_admin_creation_page(testapp, endpoint):
    """ helper function that verifies that we see the admin creation page """
    response = testapp.get(endpoint, expect_errors=True).maybe_follow()
    assert response.status_code == 200, "Response Status Failure: {}".format(endpoint)
    assert "<!-- Route: /create_admin -->" in response


def test_sees_admin_creation_form(testapp):
    """ No Admin user exists: user sees the admin creation page """
    # Delete all admin users to show the admin creation form
    for each_admin in User.query.filter_by(role=1).all():
        each_admin.delete()
    expected_body_msg = "<!-- Route: /create_admin -->"
    assert expected_body_msg in testapp.get('/').maybe_follow()


def test_does_not_see_admin_creation_form(testapp):
    """ Admin user exists: user sees the normal login page """
    expected_body_msg = "<!-- Route: /login -->"
    assert expected_body_msg in testapp.get('/').maybe_follow()


def test_routes_when_not_logged_in(testapp):
    """
    Verifies behavior of these endpoints when not logged in.
    All endpoint requests should redirect to the login page.
    """
    routes = [
        '',
        'admin/backup',
        'admin/statistics',
        'admin/upgrade',
        'async/0/0/0/0',
        'camera',
        'dl/0/0',
        'data'
        'daemonactive',
        'export',
        'function',
        'gpiostate',
        'graph',
        'graph-async',
        'help',
        'info',
        'last/0/0/0',
        'lcd',
        'live',
        'logout',
        'logview',
        'method',
        'method-build/0',
        'method-data/0',
        'method-delete/0',
        'past/0/0/0',
        'output',
        'remote/setup',
        'settings/alerts',
        'settings/camera',
        'settings/general',
        'settings/users',
        'systemctl/restart',
        'systemctl/shutdown',
        'timer',
        'usage',
        'video_feed/0'
    ]
    for route in routes:
        redirects_to_login_page(testapp=testapp, endpoint='/{add}'.format(add=route))


# ---------------------------
#   Tests Logged in as Admin
# ---------------------------
@mock.patch('mycodo.mycodo_flask.authentication_routes.login_log')
def test_routes_logged_in_as_admin(_, testapp):
    """ Verifies behavior of these endpoints for a logged in admin user """
    login_user(testapp, 'admin', '53CR3t_p4zZW0rD')

    # Test if the navigation bar is seen on the main page
    sees_navbar(testapp)

    # Test all endpoints
    routes = [
        ('admin/backup', '<!-- Route: /admin/backup -->'),
        ('admin/statistics', '<!-- Route: /admin/statistics -->'),
        ('admin/upgrade', '<!-- Route: /admin/upgrade -->'),
        ('settings/alerts', '<!-- Route: /settings/alerts -->'),
        ('settings/camera', '<!-- Route: /settings/camera -->'),
        ('settings/general', '<!-- Route: /settings/general -->'),
        ('settings/users', '<!-- Route: /settings/users -->'),
        ('calibration', '<!-- Route: /calibration -->'),
        ('camera', '<!-- Route: /camera -->'),
        ('data', '<!-- Route: /data -->'),
        ('export', '<!-- Route: /export -->'),
        ('function', '<!-- Route: /function -->'),
        ('graph', '<!-- Route: /graph -->'),
        ('graph-async', '<!-- Route: /graph-async -->'),
        ('help', '<h1 id="mycodo-manual">Mycodo Manual</h1>'),
        ('info', '<!-- Route: /info -->'),
        ('lcd', '<!-- Route: /lcd -->'),
        ('live', '<!-- Route: /live -->'),
        ('logview', '<!-- Route: /logview -->'),
        ('method', '<!-- Route: /method -->'),
        ('method-build/-1', 'admin logged in'),
        ('output', '<!-- Route: /output -->'),
        ('remote/setup', '<!-- Route: /remote/setup -->'),
        ('timer', '<!-- Route: /timer -->'),
        ('usage', '<!-- Route: /usage -->'),
        ('usage_reports', '<!-- Route: /usage_reports -->')
    ]
    for route in routes:
        response = testapp.get('/{add}'.format(add=route[0])).maybe_follow()
        assert response.status_code == 200, "Endpoint Tested: {page}".format(page=route[0])
        assert route[1] in response, "Unexpected HTTP Response: \n{body}".format(body=response.body)


# @mock.patch('mycodo.mycodo_flask.authentication_routes.login_log')
# def test_add_sensor_logged_in_as_admin(_, testapp):
#     """ Verifies adding a sensor as a logged in admin user """
#     login_user(testapp, 'admin', '53CR3t_p4zZW0rD')
#
#     response = add_sensor(testapp)
#
#     # Verify success message flashed
#     print(response)
#     assert "RPi Sensor with ID" in response
#     assert "successfully added" in response
#
#     # Verify data was entered into the database
#     for each_sensor in Sensor.query.all():
#         assert 'RPi' in each_sensor.name, "Sensor name doesn't match: {}".format(each_sensor.name)


# ---------------------------
#   Tests Logged in as Guest
# ---------------------------
@mock.patch('mycodo.mycodo_flask.authentication_routes.login_log')
def test_routes_logged_in_as_guest(_, testapp):
    """ Verifies behavior of these endpoints for a logged in guest user """
    login_user(testapp, 'guest', '53CR3t_p4zZW0rD')

    # Test if the navigation bar is seen on the main page
    sees_navbar(testapp)

    # Test all endpoints
    routes = [
        ('admin/backup', '<!-- Route: /live -->'),
        ('admin/upgrade', '<!-- Route: /live -->'),
        ('admin/statistics', '<!-- Route: /live -->'),
        ('remote/setup', '<!-- Route: /live -->'),
        ('settings/alerts', '<!-- Route: /live -->'),
        ('settings/camera', '<!-- Route: /live -->'),
        ('settings/general', '<!-- Route: /live -->'),
        ('settings/users', '<!-- Route: /live -->'),
        ('systemctl/restart', '<!-- Route: /live -->'),
        ('systemctl/shutdown', '<!-- Route: /live -->')
    ]
    for route in routes:
        response = testapp.get('/{add}'.format(add=route[0])).maybe_follow()
        assert response.status_code == 200, "Endpoint Tested: {page}".format(page=route[0])
        assert route[1] in response, "Unexpected HTTP Response: \n{body}".format(body=response.body)


def create_user(mycodo_db, role, name, password):
    """ Create fake admin user """
    new_user = UserFactory()
    new_user.name = name
    new_user.set_password(password)
    new_user.role = role
    mycodo_db.add(new_user)
    mycodo_db.commit()
    return new_user


def add_sensor(testapp, sensor_type='RPi', qty=1):
    """ Go to the sensor page and create one or more sensors """
    form = testapp.get('/input').maybe_follow().forms['new_sensor_form']
    form['numberSensors'] = qty
    form.select(name='sensor', value=sensor_type)
    response = form.submit().maybe_follow()
    # response.showbrowser()
    return response


def sees_navbar(testapp):
    """ Test if the navbar is seen at the endpoint '/' """
    # Test if the navigation bar is seen on the main page
    response = testapp.get('/').maybe_follow()
    assert response.status_code == 200
    navbar_strings = [
        'Asynchronous Graphs',
        'Cameras',
        'Configure',
        'Data',
        'Export',
        'Func',
        'Info',
        'Live Graphs',
        'LCDs',
        'Live Measurements',
        'Logout',
        'Mycodo Logs',
        'Methods',
        'Output Usage',
        'Output Usage Reports',
        'Remote Admin',
        'System Information',
        'Timer',
        'Upgrade'
    ]
    assert all(
        x in response for x in navbar_strings), "Not all navbar strings found at '/' endpoint. Found: {body}".format(
        body=response.body)
