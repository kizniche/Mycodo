# coding=utf-8
""" functional tests for flask endpoints """
import mock

from mycodo.config import MATH_INFO
from mycodo.databases.models import Input
from mycodo.databases.models import Math
from mycodo.databases.models import User
from mycodo.mycodo_flask.utils.utils_general import generate_form_input_list
from mycodo.tests.software_tests.conftest import login_user
from mycodo.tests.software_tests.factories import UserFactory
from mycodo.utils.inputs import parse_input_information


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


def returns_401_unauthorized(testapp, endpoint):
    """ helper function that verifies 401 is returned """
    response = testapp.get(
        endpoint,
        headers={'Accept': 'application/vnd.mycodo.v1+json'},
        expect_errors=True).maybe_follow()
    assert response.status_code == 401, "Response Status Failure: {}".format(endpoint)


def test_sees_admin_creation_form(testapp):
    """ No Admin user exists: user sees the admin creation page """
    print("\nTest: test_sees_admin_creation_form")
    # Delete all admin users to show the admin creation form
    for each_admin in User.query.filter_by(role_id=1).all():
        each_admin.delete()
    expected_body_msg = "<!-- Route: /create_admin -->"
    assert expected_body_msg in testapp.get('/').maybe_follow()


def test_does_not_see_admin_creation_form(testapp):
    """ Admin user exists: user sees the normal login page """
    print("\nTest: test_does_not_see_admin_creation_form")
    expected_body_msg = "<!-- Route: /login -->"
    assert expected_body_msg in testapp.get('/').maybe_follow()


def test_routes_when_not_logged_in(testapp):
    """
    Verifies behavior of these endpoints when not logged in.
    All endpoint requests should redirect to the login page.
    """
    print("\nTest: test_routes_when_not_logged_in")
    routes = [
        '',
        'admin/backup',
        'admin/statistics',
        'admin/upgrade',
        'async/0/0/0/0/0',
        'camera',
        'dl/0/0',
        'data',
        'daemonactive',
        'dashboard',
        'export',
        'function',
        'outputstate',
        'graph-async',
        'info',
        'last/0/0/0/0',
        'lcd',
        'live',
        'logout',
        'logview',
        'method',
        'method-build/0',
        'method-data/0',
        'method-delete/0',
        'past/0/0/0/0',
        'output',
        'remote/setup',
        'settings/alerts',
        'settings/general',
        'settings/input',
        'settings/measurement',
        'settings/users',
        'systemctl/restart',
        'systemctl/shutdown',
        'usage',
        'video_feed/0'
    ]
    for route in routes:
        redirects_to_login_page(testapp=testapp, endpoint='/{add}'.format(add=route))


def test_api_when_not_logged_in(testapp):
    """
    Verifies behavior of these API endpoints when not logged in.
    All API endpoint requests should return 401 (unauthorized).
    """
    print("\nTest: test_api_when_not_logged_in")
    routes = [
        'choices/controllers',
        'choices/inputs/measurements',
        'choices/output/devices',
        'choices/output/measurements',
        'choices/pid/measurements',
        'settings/device_measurements',
        'settings/inputs',
        'settings/measurements',
        'settings/outputs',
        'settings/pids',
        'settings/units',
        'settings/users'
    ]
    for route in routes:
        returns_401_unauthorized(testapp=testapp, endpoint='/api/{add}'.format(add=route))


def test_api_docs_when_not_logged_in(testapp):
    """
    Verifies behavior of these API endpoints when not logged in.
    API docs endpoint endpoint requests should return 200.
    """
    response = testapp.get('/api').maybe_follow()
    assert response.status_code == 200, "Endpoint Tested: /api"
    assert 'Mycodo API' in response, "Unexpected HTTP Response: \n{body}".format(body=response.body)


# ---------------------------
#   Tests Logged in as Admin
# ---------------------------
@mock.patch('mycodo.mycodo_flask.routes_authentication.login_log')
def test_routes_logged_in_as_admin(_, testapp):
    """ Verifies behavior of these endpoints for a logged in admin user """
    print("\nTest: test_routes_logged_in_as_admin")

    print("test_routes_logged_in_as_admin: login_user(testapp, 'admin', '53CR3t_p4zZW0rD')")
    login_user(testapp, 'admin', '53CR3t_p4zZW0rD')

    # Test if the navigation bar is seen on the main page
    sees_navbar(testapp)

    # Test all endpoints
    routes = [
        ('api', 'Mycodo API'),
        ('admin/backup', '<!-- Route: /admin/backup -->'),
        ('admin/statistics', '<!-- Route: /admin/statistics -->'),
        ('admin/upgrade', '<!-- Route: /admin/upgrade -->'),
        ('settings/alerts', '<!-- Route: /settings/alerts -->'),
        ('settings/general', '<!-- Route: /settings/general -->'),
        ('settings/input', '<!-- Route: /settings/input -->'),
        ('settings/measurement', '<!-- Route: /settings/measurement -->'),
        ('settings/users', '<!-- Route: /settings/users -->'),
        ('calibration', '<!-- Route: /calibration -->'),
        ('camera', '<!-- Route: /camera -->'),
        ('dashboard', '<!-- Route: /dashboard -->'),
        ('data', '<!-- Route: /data -->'),
        ('export', '<!-- Route: /export -->'),
        ('function', '<!-- Route: /function -->'),
        ('graph-async', '<!-- Route: /graph-async -->'),
        ('info', '<!-- Route: /info -->'),
        ('lcd', '<!-- Route: /lcd -->'),
        ('live', '<!-- Route: /live -->'),
        ('logview', '<!-- Route: /logview -->'),
        ('method', '<!-- Route: /method -->'),
        ('method-build/-1', 'admin logged in'),
        ('notes', '<!-- Route: /notes -->'),
        ('note_edit/0', 'admin logged in'),
        ('output', '<!-- Route: /output -->'),
        ('remote/setup', '<!-- Route: /remote/setup -->'),
        ('setup_atlas_ph', '<!-- Route: /setup_atlas_ph -->'),
        ('setup_ds_resolution', '<!-- Route: /setup_ds_resolution -->'),
        ('usage', '<!-- Route: /usage -->'),
        ('usage_reports', '<!-- Route: /usage_reports -->')
    ]

    for index, route in enumerate(routes):
        print("test_routes_logged_in_as_admin: Test Route ({}/{}): testapp.get('/{}').maybe_follow()".format(
            index + 1, len(routes), route[0]))
        response = testapp.get('/{add}'.format(add=route[0])).maybe_follow()
        assert response.status_code == 200, "Endpoint Tested: {page}".format(page=route[0])
        assert route[1] in response, "Unexpected HTTP Response: \n{body}".format(body=response.body)


@mock.patch('mycodo.mycodo_flask.routes_authentication.login_log')
def test_api_logged_in_as_admin(_, testapp):
    """ Verifies behavior of these API endpoints for a logged in admin user """
    print("\nTest: test_api_logged_in_as_admin")

    print("test_routes_logged_in_as_admin: login_user(testapp, 'admin', '53CR3t_p4zZW0rD')")
    login_user(testapp, 'admin', '53CR3t_p4zZW0rD')

    # Test all endpoints
    routes = [
        ('choices/controllers', '"choices controllers":'),
        ('choices/inputs/measurements', '"choices inputs measurements":'),
        ('choices/outputs/devices', '"choices outputs devices":'),
        ('choices/outputs/measurements', '"choices outputs measurements":'),
        ('choices/pids/measurements', '"choices pids measurements":'),
        ('settings/device_measurements', '"device measurements":'),
        ('settings/inputs', '"inputs":'),
        ('settings/measurements', '"measurements":'),
        ('settings/outputs', '"outputs":'),
        ('settings/pids', '"pids":'),
        ('settings/units', '"units":'),
        ('settings/users', '"users":'),
    ]

    for index, route in enumerate(routes):
        print("test_routes_logged_in_as_admin: Test Route ({}/{}): testapp.get('/api/{}').maybe_follow()".format(
            index + 1, len(routes), route[0]))
        response = testapp.get(
            '/api/{add}'.format(add=route[0]),
            headers={'Accept': 'application/vnd.mycodo.v1+json'})
        assert response.status_code == 200, "Endpoint Tested: {page}".format(page=route[0])
        assert route[1] in response, "Unexpected HTTP Response: \n{body}".format(body=response.body)


@mock.patch('mycodo.mycodo_flask.routes_authentication.login_log')
def test_add_all_data_devices_logged_in_as_admin(_, testapp):
    """ Verifies adding all inputs as a logged in admin user """
    print("\nTest: test_add_all_data_devices_logged_in_as_admin")
    login_user(testapp, 'admin', '53CR3t_p4zZW0rD')

    # Add All Inputs
    input_count = 0

    dict_inputs = parse_input_information()
    list_inputs_sorted = generate_form_input_list(dict_inputs)

    choices_input = []
    for each_input in list_inputs_sorted:
        if 'interfaces' not in dict_inputs[each_input]:
            choices_input.append('{inp},'.format(inp=each_input))
        else:
            for each_interface in dict_inputs[each_input]['interfaces']:
                choices_input.append('{inp},{int}'.format(inp=each_input, int=each_interface))

    for index, each_input in enumerate(choices_input):
        choice_name = each_input.split(',')[0]
        print("test_add_all_data_devices_logged_in_as_admin: Adding Input ({}/{}): {}".format(
            index + 1, len(choices_input), each_input))
        response = add_data(testapp, data_type='input', input_type=each_input)

        # Verify success message flashed
        assert "{} Input with ID".format(choice_name) in response
        assert "successfully added" in response

        # Verify data was entered into the database
        input_count += 1
        assert Input.query.count() == input_count, "Number of Inputs doesn't match: In DB {}, Should be: {}".format(Input.query.count(), input_count)

        input_dev = Input.query.filter(Input.id == input_count).first()
        assert dict_inputs[choice_name]['input_name'] in input_dev.name, "Input name doesn't match: {}".format(choice_name)

    # Add All Maths
    math_count = 0
    for index, each_math in enumerate(MATH_INFO.keys()):
        print("test_add_all_data_devices_logged_in_as_admin: Adding Math ({}/{}): {}".format(
            index + 1, len(MATH_INFO.keys()), each_math))
        response = add_data(testapp, data_type='math', input_type=each_math)

        # Verify success message flashed
        assert "{} Math with ID".format(each_math) in response
        assert "successfully added" in response

        # Verify data was entered into the database
        math_count += 1
        actual_count = Math.query.count()
        assert actual_count == math_count, "Number of Maths don't match: In DB {}, Should be: {}".format(actual_count, math_count)

        math_dev = Math.query.filter(Math.id == math_count).first()
        assert each_math in math_dev.math_type, "Math type doesn't match: {}".format(each_math)


# ---------------------------
#   Tests Logged in as Guest
# ---------------------------
@mock.patch('mycodo.mycodo_flask.routes_authentication.login_log')
def test_routes_logged_in_as_guest(_, testapp):
    """ Verifies behavior of these endpoints for a logged in guest user """
    print("\nTest: test_routes_logged_in_as_guest")

    print("test_routes_logged_in_as_admin: login_user(testapp, 'guest', '53CR3t_p4zZW0rD')")
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
        ('settings/diagnostic', '<!-- Route: /live -->'),
        ('settings/general', '<!-- Route: /live -->'),
        ('settings/measurement', '<!-- Route: /live -->'),
        ('settings/users', '<!-- Route: /live -->'),
        ('systemctl/restart', '<!-- Route: /live -->'),
        ('systemctl/shutdown', '<!-- Route: /live -->')
    ]
    for index, route in enumerate(routes):
        print("test_routes_logged_in_as_guest: Test Route ({}/{}): testapp.get('/{}').maybe_follow()".format(
            index + 1, len(routes), route[0]))
        response = testapp.get('/{add}'.format(add=route[0])).maybe_follow()
        assert response.status_code == 200, "Endpoint Tested: {page}".format(page=route[0])
        assert route[1] in response, "Unexpected HTTP Response: \n{body}".format(body=response.body)


def create_user(mycodo_db, role_id, name, password):
    """ Create fake admin user """
    new_user = UserFactory()
    new_user.name = name
    new_user.set_password(password)
    new_user.role_id = role_id
    mycodo_db.add(new_user)
    mycodo_db.commit()
    return new_user


def add_data(testapp, data_type='input', input_type='RPi'):
    """ Go to the data page and create one or more inputs """
    response = None
    if data_type == 'input':
        form = testapp.get('/data').maybe_follow().forms['new_input_form']
        form.select(name='input_type', value=input_type)
        response = form.submit(name='input_add', value='Add').maybe_follow()
    elif data_type == 'math':
        form = testapp.get('/data').maybe_follow().forms['new_math_form']
        form.select(name='math_type', value=input_type)
        response = form.submit(name='math_add', value='Add').maybe_follow()
    # response.showbrowser()
    return response


def sees_navbar(testapp):
    """ Test if the navbar is seen at the endpoint '/' """
    # Test if the navigation bar is seen on the main page
    print("sees_navbar(testapp): {}".format(testapp))
    response = testapp.get('/').maybe_follow()
    assert response.status_code == 200
    navbar_strings = [
        'Asynchronous Graphs',
        'Calibration & Setup',
        'Camera',
        'Configure',
        'Dashboard',
        'Data',
        'Export',
        'Function',
        'LCD',
        'Live',
        'Logout',
        'Mycodo Logs',
        'Method',
        'Note',
        'Output',
        'Energy Usage',
        'Energy Usage Reports',
        'Remote Admin',
        'System Information',
        'Upgrade'
    ]
    assert all(
        x in response for x in navbar_strings), "Not all navbar strings found at '/' endpoint. Found: {body}".format(
        body=response.body)
