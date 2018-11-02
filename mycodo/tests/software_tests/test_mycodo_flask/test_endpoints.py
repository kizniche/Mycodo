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


def test_sees_admin_creation_form(testapp):
    """ No Admin user exists: user sees the admin creation page """
    # Delete all admin users to show the admin creation form
    for each_admin in User.query.filter_by(role_id=1).all():
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
        'async/0/0/0/0/0/0',
        'camera',
        'dl/0/0',
        'data',
        'daemonactive',
        'dashboard',
        'export',
        'function',
        'gpiostate',
        'graph-async',
        'help',
        'info',
        'last/0/0/0/0/0',
        'lcd',
        'live',
        'logout',
        'logview',
        'method',
        'method-build/0',
        'method-data/0',
        'method-delete/0',
        'past/0/0/0/0/0',
        'output',
        'remote/setup',
        'settings/alerts',
        'settings/camera',
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


# ---------------------------
#   Tests Logged in as Admin
# ---------------------------
@mock.patch('mycodo.mycodo_flask.routes_authentication.login_log')
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
        ('help', '<h1 class="title">Mycodo Manual</h1>'),
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
        ('usage', '<!-- Route: /usage -->'),
        ('usage_reports', '<!-- Route: /usage_reports -->')
    ]
    for route in routes:
        response = testapp.get('/{add}'.format(add=route[0])).maybe_follow()
        assert response.status_code == 200, "Endpoint Tested: {page}".format(page=route[0])
        assert route[1] in response, "Unexpected HTTP Response: \n{body}".format(body=response.body)


@mock.patch('mycodo.mycodo_flask.routes_authentication.login_log')
def test_add_all_data_devices_logged_in_as_admin(_, testapp):
    """ Verifies adding all inputs as a logged in admin user """
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

    for each_input in choices_input:
        choice_name = each_input.split(',')[0]
        print("Testing {}".format(each_input))
        response = add_data(testapp, data_type='input', input_type=each_input)

        # Verify success message flashed
        assert "{} Input with ID".format(choice_name) in response
        assert "successfully added" in response

        # Verify data was entered into the database
        input_count += 1
        assert Input.query.count() == input_count, "Number of Inputs doesn't match: In DB {}, Should be: {}".format(Input.query.count(), input_count)

        input_dev = Input.query.filter(Input.id == input_count).first()
        assert choice_name in input_dev.name, "Input name doesn't match: {}".format(choice_name)

    # Add All Maths
    math_count = 0
    for each_math, each_data in MATH_INFO.items():
        response = add_data(testapp, data_type='math', input_type=each_math)

        # Verify success message flashed
        assert "{} Math with ID".format(each_math) in response
        assert "successfully added" in response

        # Verify data was entered into the database
        math_count += 1
        actual_count = Math.query.count()
        assert actual_count == math_count, "Number of Maths doesn't match: In DB {}, Should be: {}".format(actual_count, math_count)

        math_dev = Math.query.filter(Math.id == math_count).first()
        assert each_data['name'] in math_dev.name, "Math name doesn't match: {}".format(each_math)


# ---------------------------
#   Tests Logged in as Guest
# ---------------------------
@mock.patch('mycodo.mycodo_flask.routes_authentication.login_log')
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
        ('settings/diagnostic', '<!-- Route: /live -->'),
        ('settings/general', '<!-- Route: /live -->'),
        ('settings/measurement', '<!-- Route: /live -->'),
        ('settings/users', '<!-- Route: /live -->'),
        ('systemctl/restart', '<!-- Route: /live -->'),
        ('systemctl/shutdown', '<!-- Route: /live -->')
    ]
    for route in routes:
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
        response = form.submit(name='input_add', value='Add Input').maybe_follow()
    elif data_type == 'math':
        form = testapp.get('/data').maybe_follow().forms['new_math_form']
        form.select(name='math_type', value=input_type)
        response = form.submit(name='math_add', value='Add Math').maybe_follow()
    # response.showbrowser()
    return response


def sees_navbar(testapp):
    """ Test if the navbar is seen at the endpoint '/' """
    # Test if the navigation bar is seen on the main page
    response = testapp.get('/').maybe_follow()
    assert response.status_code == 200
    navbar_strings = [
        'Async',
        'Calibration & Setup',
        'Cam',
        'Configure',
        'Dash',
        'Data',
        'Export',
        'Functions',
        'LCDs',
        'Live',
        'Logout',
        'Mycodo Logs',
        'Methods',
        'Notes',
        'Outputs',
        'Output Usage',
        'Output Usage Reports',
        'Remote Admin',
        'System Information',
        'Upgrade'
    ]
    assert all(
        x in response for x in navbar_strings), "Not all navbar strings found at '/' endpoint. Found: {body}".format(
        body=response.body)
