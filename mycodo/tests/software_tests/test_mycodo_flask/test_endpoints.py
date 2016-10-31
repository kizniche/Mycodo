# coding=utf-8
""" functional tests for flask endpoints """
import mock
from mycodo.tests.software_tests.factories import UserFactory
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
        'async',
        'backup',
        'camera',
        'dl',
        'daemon_active',
        'gpiostate',
        'graph',
        'graph-async',
        'help',
        'info',
        'last',
        'lcd',
        'live',
        'log',
        'logview',
        'method',
        'method-build',
        'method-data',
        'method-delete',
        'notes',
        'past',
        'pid',
        'relay',
        'remote/setup',
        'sensor',
        'settings/alerts',
        'settings/camera',
        'settings/general',
        'settings/users',
        'systemctl',
        'timer',
        'upgrade',
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


# -----------------------
#   Logged In Tests
# -----------------------
@mock.patch('mycodo.mycodo_flask.authentication.views.login_log')
def test_routes_logged_in_as_admin(_, testapp, user_db):
    """ Verifies behavior of these endpoints for a logged in admin user """
    # Create admin user and log in
    admin_user = create_user_admin(user_db, 'admin', 'secret_pass')
    login_user(testapp, admin_user.user_name, 'secret_pass')

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
    assert all(x in response for x in navbar_strings), "Not all navbar strings found at '/' endpoint. Found: {body}".format(body=response.body)

    # Test all endpoints
    routes = [
        ('camera', '<!-- Route: /camera -->'),
        ('graph', '<!-- Route: /graph -->'),
        ('graph-async', '<!-- Route: /graph-async -->'),
        ('help', '<!-- Route: /help -->'),
        ('lcd', '<!-- Route: /lcd -->'),
        ('live', '<!-- Route: /live -->'),
        ('log', '<!-- Route: /log -->'),
        ('method', '<!-- Route: /method -->'),
        ('pid', '<!-- Route: /pid -->'),
        ('relay', '<!-- Route: /relay -->'),
        ('remote/setup', '<!-- Route: /remote/setup -->'),
        ('sensor', '<!-- Route: /sensor -->'),
        ('timer', '<!-- Route: /timer -->'),
        ('method-build/1/0', 'admin logged in')
    ]
    for route in routes:
        response = testapp.get('/{add}'.format(add=route[0])).maybe_follow()
        assert response.status_code == 200, "Endpoint Tested: {page}".format(page=route[0])
        assert route[1] in response, "Unexpected HTTP Response: \n{body}".format(body=response.body)


def create_user_admin(user_db, name, password):
    """ Create fake admin user """
    admin_user = UserFactory()
    admin_user.user_name = name
    admin_user.set_password(password)
    user_db.add(admin_user)
    user_db.commit()
    return admin_user
