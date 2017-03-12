# coding=utf-8
""" functional tests for flask endpoints """
import pytest
import mock
from mycodo.databases.models import Sensor

from mycodo.tests.software_tests.factories import UserFactory


# ----------------------
#   Non-Logged In Tests
# ----------------------
def redirects_to_login_page(testapp, endpoint):
    """ helper function that verifies that we see the login page """
    response = testapp.get(endpoint, expect_errors=True).maybe_follow()
    assert response.status_code == 200, "Response Status Failure: {}".format(endpoint)
    assert "Mycodo Login" in response


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
        'daemonactive',
        'export',
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
        'notes',
        'past/0/0/0',
        'pid',
        'relay',
        'remote/setup',
        'sensor',
        'settings/alerts',
        'settings/camera',
        'settings/general',
        'settings/users',
        'systemctl/restart',
        'systemctl/shutdown',
        'timer',
        'usage',
        'video_feed'
    ]
    for route in routes:
        redirects_to_login_page(testapp=testapp, endpoint='/{add}'.format(add=route))


def test_sees_admin_creation_form(testapp_no_admin_user):
    """ No Admin user exists: user sees the admin creation page """
    expected_body_msg = "<!-- Route: /create_admin -->"
    assert expected_body_msg in testapp_no_admin_user.get('/').maybe_follow()


def test_does_not_see_admin_creation_form(testapp):
    """ Admin user exists: user sees the normal login page """
    expected_body_msg = "<!-- Route: /login -->"
    assert expected_body_msg in testapp.get('/').maybe_follow()


# ---------------------------
#   Tests Logged in as Admin
# ---------------------------
@mock.patch('mycodo.mycodo_flask.authentication_routes.login_log')
def test_routes_logged_in_as_admin(_, testapp, mycodo_db):
    """ Verifies behavior of these endpoints for a logged in admin user """
    # Create admin user and log in
    admin_user = create_user(mycodo_db, 1, 'name_admin', 'secret_pass')
    login_user(testapp, admin_user.name, 'secret_pass')

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
        ('camera', '<!-- Route: /camera -->'),
        ('export', '<!-- Route: /export -->'),
        ('graph', '<!-- Route: /graph -->'),
        ('graph-async', '<!-- Route: /graph-async -->'),
        ('help', '<!-- Route: /help -->'),
        ('info', '<!-- Route: /info -->'),
        ('lcd', '<!-- Route: /lcd -->'),
        ('live', '<!-- Route: /live -->'),
        ('logview', '<!-- Route: /logview -->'),
        ('method', '<!-- Route: /method -->'),
        ('method-build/1/0', 'admin logged in'),
        ('notes', '<!-- Route: /notes -->'),
        ('pid', '<!-- Route: /pid -->'),
        ('relay', '<!-- Route: /relay -->'),
        ('remote/setup', '<!-- Route: /remote/setup -->'),
        ('sensor', '<!-- Route: /sensor -->'),
        ('timer', '<!-- Route: /timer -->'),
        ('usage', '<!-- Route: /usage -->')
    ]
    for route in routes:
        response = testapp.get('/{add}'.format(add=route[0])).maybe_follow()
        assert response.status_code == 200, "Endpoint Tested: {page}".format(page=route[0])
        assert route[1] in response, "Unexpected HTTP Response: \n{body}".format(body=response.body)


@mock.patch('mycodo.mycodo_flask.authentication_routes.login_log')
def test_add_sensor_logged_in_as_admin(_, testapp, mycodo_db):
    """ Verifies behavior of these endpoints for a logged in admin user """
    # Create admin user and log in
    admin_user = create_user(mycodo_db, 1, 'name_admin', 'secret_pass')
    login_user(testapp, admin_user.name, 'secret_pass')

    response = add_sensor(testapp)

    # Verify success message flashed
    assert "RPi Sensor with ID" in response
    assert "successfully added" in response

    # Verify data was entered into the database
    for each_sensor in Sensor.query.all():
        assert 'RPi' in each_sensor.name, "Sensor name doesn't match: {}".format(each_sensor.name)


# ---------------------------
#   Tests Logged in as Guest
# ---------------------------
@mock.patch('mycodo.mycodo_flask.authentication_routes.login_log')
def test_routes_logged_in_as_guest(_, testapp, mycodo_db):
    """ Verifies behavior of these endpoints for a logged in guest user """
    # Create guest user and log in
    guest_user = create_user(mycodo_db, 4, 'name_guest', 'secret_pass')
    login_user(testapp, guest_user.name, 'secret_pass')

    # Test if the navigation bar is seen on the main page
    sees_navbar(testapp)

    # Test all endpoints
    routes = [
        ('admin/backup', 'Guests are not permitted'),
        ('admin/upgrade', 'Guests are not permitted'),
        ('admin/statistics', 'Guests are not permitted'),
        ('remote/setup', 'Guests are not permitted'),
        ('settings/users', 'Guests are not permitted'),
        ('settings/alerts', 'Guests are not permitted'),
        ('systemctl/restart', 'Guests are not permitted'),
        ('systemctl/shutdown', 'Guests are not permitted')
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
    form = testapp.get('/sensor').maybe_follow().forms['new_sensor_form']
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
        'Admin',
        'Camera',
        'Configure',
        'Export Measurements',
        'Graph',
        'Help',
        'LCD',
        'Live',
        'Logout',
        'Method',
        'Mycodo Logs',
        'Notes',
        'PID',
        'Relay',
        'Relay Usage',
        'Remote Admin',
        'Sensor',
        'System Info',
        'Timer',
        'Upgrade'
    ]
    assert all(
        x in response for x in navbar_strings), "Not all navbar strings found at '/' endpoint. Found: {body}".format(
        body=response.body)
