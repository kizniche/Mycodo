# coding=utf-8
""" functional tests for flask endpoints """
import mock
from flask import (current_app,
                   session)
from mycodo import flaskforms
from mycodo import flaskutils
from mycodo.databases.mycodo_db.models import Sensor
from mycodo.tests.software_tests.factories_user import UserFactory
from mycodo.tests.software_tests.factories_mycodo import SensorFactory
from mycodo.tests.software_tests.test_mycodo_flask.conftest import login_user


# ----------------------
#   Non-Logged In Tests
# ----------------------
def redirects_to_login_page(app, endpoint):
    """ helper function that verifies that we see the login page """
    response = app.get(endpoint).maybe_follow()
    assert response.status_code == 200, "Endpoint Tested: {page}".format(page=endpoint)
    assert "Mycodo Login" in response, 'Did Not see login page.  Saw "{body}"'.format(body=response.body)


def test_routes_not_logged_in(testapp):
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
        'gpiostate',
        'graph',
        'graph-async',
        'help',
        'info',
        'last/0/0/0/0',
        'lcd',
        'live',
        'log',
        'logout',
        'logview',
        'method',
        'method-build/0/0',
        'method-data/0/0',
        'method-delete/0',
        'notes',
        'past/0/0/0/0',
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
        redirects_to_login_page(app=testapp,
                                endpoint='/{add}'.format(add=route))


def test_sees_admin_creation_form(testapp_no_admin_user):
    """ No Admin user exists: user sees the admin creation page """
    expected_body_msg = "Mycodo was unable to find an admin user in the user database."
    assert expected_body_msg in testapp_no_admin_user.get('/').maybe_follow()


def test_does_not_see_admin_creation_form(testapp):
    """ Admin user exists: user sees the normal login page """
    expected_body_msg = "Mycodo was unable to find an admin user in the user database."
    assert expected_body_msg not in testapp.get('/').maybe_follow()


# ---------------------------
#   Tests Logged in as Admin
# ---------------------------
@mock.patch('mycodo.mycodo_flask.authentication.views.login_log')
def test_routes_logged_in_as_admin(_, testapp, user_db):
    """ Verifies behavior of these endpoints for a logged in admin user """
    # Create admin user and log in
    admin_user = create_user(user_db, 'admin', 'name_admin', 'secret_pass')
    login_user(testapp, admin_user.user_name, 'secret_pass')

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
        ('graph', '<!-- Route: /graph -->'),
        ('graph-async', '<!-- Route: /graph-async -->'),
        ('help', '<!-- Route: /help -->'),
        ('lcd', '<!-- Route: /lcd -->'),
        ('live', '<!-- Route: /live -->'),
        ('log', '<!-- Route: /log -->'),
        ('method', '<!-- Route: /method -->'),
        ('method-build/1/0', 'admin logged in'),
        ('pid', '<!-- Route: /pid -->'),
        ('relay', '<!-- Route: /relay -->'),
        ('remote/setup', '<!-- Route: /remote/setup -->'),
        ('sensor', '<!-- Route: /sensor -->'),
        ('timer', '<!-- Route: /timer -->')
    ]
    for route in routes:
        response = testapp.get('/{add}'.format(add=route[0])).maybe_follow()
        assert response.status_code == 200, "Endpoint Tested: {page}".format(page=route[0])
        assert route[1] in response, "Unexpected HTTP Response: \n{body}".format(body=response.body)


@mock.patch('mycodo.mycodo_flask.authentication.views.login_log')
def test_adding_sensor_logged_in_as_admin(_, testapp, user_db, mycodo_db):
    """ Verifies behavior of these endpoints for a logged in admin user """
    # Create admin user and log in
    admin_user = create_user(user_db, 'admin', 'name_admin', 'secret_pass')
    login_user(testapp, admin_user.user_name, 'secret_pass')
    session['user_group'] = 'admin'

    # Create WTForms form and populate data
    formAddSensor = flaskforms.AddSensor()
    formAddSensor.sensor.data = 'RPiCPULoad'
    formAddSensor.numberSensors.data = 1

    # Submit form data to create sensor in database
    flaskutils.sensor_add(formAddSensor, display_order=[])
    # Verify data was entered into database (doesn't work)
    sensor = flaskutils.db_retrieve_table(current_app.config['MYCODO_DB_PATH'], Sensor)
    for each_sensor in sensor:
        print("01 Testing return sensor name: {}".format(each_sensor.name))

    # Alternate method to enter data into database
    new_sensor = SensorFactory()
    new_sensor.name = 'name'
    mycodo_db.add(new_sensor)
    mycodo_db.commit()
    # Verify data was entered into database (does work)
    sensor = flaskutils.db_retrieve_table(current_app.config['MYCODO_DB_PATH'], Sensor)
    for each_sensor in sensor:
        print("02 Testing return sensor name: {}".format(each_sensor.name))



# ---------------------------
#   Tests Logged in as Guest
# ---------------------------
@mock.patch('mycodo.mycodo_flask.authentication.views.login_log')
def test_routes_logged_in_as_guest(_, testapp, user_db):
    """ Verifies behavior of these endpoints for a logged in guest user """
    # Create guest user and log in
    guest_user = create_user(user_db, 'guest', 'name_guest', 'secret_pass')
    login_user(testapp, guest_user.user_name, 'secret_pass')

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


def create_user(user_db, restriction, name, password):
    """ Create fake admin user """
    new_user = UserFactory()
    new_user.user_name = name
    new_user.set_password(password)
    new_user.user_restriction = restriction
    user_db.add(new_user)
    user_db.commit()
    return new_user


def sees_navbar(testapp):
    """ Test if the navbar is seen at the endpoint '/' """
    # Test if the navigation bar is seen on the main page
    response = testapp.get('/').maybe_follow()
    assert response.status_code == 200
    navbar_strings = [
        'Live',
        'Graph',
        'Sensor',
        'Relay',
        'Method',
        'PID',
        'Timer',
        'Help',
        'Admin'
    ]
    assert all(
        x in response for x in navbar_strings), "Not all navbar strings found at '/' endpoint. Found: {body}".format(
        body=response.body)
