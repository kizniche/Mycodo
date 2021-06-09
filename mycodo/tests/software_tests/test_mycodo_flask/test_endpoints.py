# coding=utf-8
""" functional tests for flask endpoints """
import base64
import json
import random
import time

import mock

from mycodo.databases.models import CustomController
from mycodo.databases.models import Input
from mycodo.databases.models import Output
from mycodo.databases.models import User
from mycodo.mycodo_flask.utils.utils_general import choices_custom_functions
from mycodo.mycodo_flask.utils.utils_general import generate_form_input_list
from mycodo.mycodo_flask.utils.utils_general import generate_form_output_list
from mycodo.tests.software_tests.conftest import login_user
from mycodo.tests.software_tests.factories import UserFactory
from mycodo.utils.inputs import parse_input_information
from mycodo.utils.outputs import parse_output_information


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
    print("\nTest: test_sees_admin_creation_form")
    # Delete all admin users to show the admin creation form
    for each_admin in User.query.filter_by(role_id=1).all():
        each_admin.delete()
    expected_body_msg = "<!-- Route: /create_admin -->"
    assert expected_body_msg in testapp.get('/').maybe_follow()


def test_does_not_see_admin_creation_form(testapp):
    """ Admin user exists: user sees the normal login page """
    print("\nTest: test_does_not_see_admin_creation_form")
    expected_body_msg = "<!-- Route: /login_password -->"
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
        'daemonactive',
        'dashboard',
        'export',
        'function',
        'outputstate',
        'graph-async',
        'info',
        'input',
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
    for index, route in enumerate(routes):
        print("test_routes_when_not_logged_in: Test Route ({}/{}): testapp.get('/{}').maybe_follow()".format(
            index + 1, len(routes), route))
        redirects_to_login_page(testapp=testapp, endpoint='/{add}'.format(add=route))


# ---------------
#   API Endpoints
# ---------------
api_endpoints = [
    ('choices/controllers', 'choices controllers'),
    ('choices/inputs/measurements', '"choices inputs measurements":'),
    ('choices/outputs/devices', '"choices outputs devices":'),
    ('choices/outputs/measurements', '"choices outputs measurements":'),
    ('choices/pids/measurements', '"choices pids measurements":'),
    ('settings/device_measurements', '"device measurement settings":'),
    ('settings/inputs', '"input settings":'),
    ('settings/maths', '"math settings":'),
    ('settings/measurements', '"measurement settings":'),
    ('settings/outputs', '"output settings":'),
    ('settings/pids', '"pid settings":'),
    ('settings/triggers', '"trigger settings":'),
    ('settings/units', '"unit settings":'),
    ('settings/users', '"user settings":'),
]


@mock.patch('mycodo.mycodo_flask.routes_authentication.login_log')
def test_api_logged_in_as_admin(_, testapp):
    """ Verifies behavior of these API endpoints for a logged in admin user """
    print("\nTest: test_api_logged_in_as_admin")

    print("test_routes_logged_in_as_admin: login_user(testapp, 'admin', '53CR3t_p4zZW0rD')")
    login_user(testapp, 'admin', '53CR3t_p4zZW0rD')

    # Test all endpoints
    for index, route in enumerate(api_endpoints):
        print("test_routes_logged_in_as_admin: Test Route ({}/{}): testapp.get('/api/{}')".format(
            index + 1, len(api_endpoints), route[0]))
        response = testapp.get(
            '/api/{add}'.format(add=route[0]),
            headers={'Accept': 'application/vnd.mycodo.v1+json'})
        assert response.status_code == 200, "Endpoint Tested: {page}".format(page=route[0])
        assert route[1] in response, "Unexpected HTTP Response: \n{body}".format(body=response.body)


@mock.patch('mycodo.mycodo_flask.routes_authentication.login_log')
def test_api_with_admin_apikey_in_header(_, testapp):
    """ Verifies behavior of these API endpoints with an apikey in the header """
    print("\nTest: test_api_with_admin_apikey_in_header")

    # Test all endpoints
    for index, route in enumerate(api_endpoints):
        print("test_api_with_admin_apikey_in_header: Test Route ({}/{}): testapp.get('/api/{}')".format(
            index + 1, len(api_endpoints), route[0]))
        response = testapp.get(
            '/api/{add}'.format(add=route[0]),
            headers={
                'Accept': 'application/vnd.mycodo.v1+json',
                'X-API-KEY': base64.b64encode(b'secret_admin_api_key')
            }
        )
        assert response.status_code == 200, "Endpoint Tested: {page}".format(page=route[0])
        assert route[1] in response, "Unexpected HTTP Response: \n{body}".format(body=response.body)


@mock.patch('mycodo.mycodo_flask.routes_authentication.login_log')
def test_api_measurement_post_get(_, testapp):
    """ Verifies behavior of these API endpoints with an apikey in the header to post and get a measurement """
    print("\nTest: test_api_measurement_post_get")

    # Add two measurements
    measurements_random = [random.uniform(0.0, 100000.0), random.uniform(0.0, 100000.0)]
    headers = {'Accept': 'application/vnd.mycodo.v1+json',
               'X-API-KEY': base64.b64encode(b'secret_admin_api_key')}
    for each_measurement in measurements_random:
        endpoint = 'measurements/create/testuniqueid/C/0/{val}'.format(val=each_measurement)
        print("test_api_measurement_post_get: testapp.post('/api/{ep}')".format(ep=endpoint))
        response = testapp.post('/api/{ep}'.format(ep=endpoint), headers=headers)
        assert response.status_code == 200, "Endpoint Tested: {page}".format(page=endpoint)
        assert {"message": "Success"} == json.loads(response.text), "Unexpected HTTP Response: \n{body}".format(
            body=response.body)

    # Read last stored measurement
    endpoint = 'measurements/last/testuniqueid/C/0/1000'
    print("test_api_measurement_post_get: testapp.get('/api/{ep}')".format(ep=endpoint))
    response = testapp.get('/api/{ep}'.format(ep=endpoint), headers=headers)
    assert response.status_code == 200, "Endpoint Tested: {page}".format(page=endpoint)
    assert measurements_random[1] == json.loads(response.text)['value'], "Unexpected HTTP Response: \n{body}".format(
        body=response.body)

    epoch_end = int(time.time()) + 1
    epoch_start = epoch_end - 5
    measurements_sum = 0

    # Read historical stored measurements
    endpoint = 'measurements/historical/testuniqueid/C/0/{start}/{end}'.format(start=epoch_start, end=epoch_end)
    print("test_api_measurement_post_get: testapp.get('/api/{ep}')".format(ep=endpoint))
    response = testapp.get('/api/{ep}'.format(ep=endpoint), headers=headers)
    assert response.status_code == 200, "Endpoint Tested: {page}".format(page=endpoint)
    measurement_found_first = False
    measurement_found_second = False
    for each_set in json.loads(response.text)['measurements']:
        if each_set['value'] == measurements_random[0]:
            measurement_found_first = True
            measurements_sum += each_set['value']
        if each_set['value'] == measurements_random[1]:
            measurement_found_second = True
            measurements_sum += each_set['value']
    assert measurement_found_first and measurement_found_second, "Unexpected HTTP Response: \n{body}".format(
        body=response.body)

    # Read historical stored measurements (epoch_end = 0)
    endpoint = 'measurements/historical/testuniqueid/C/0/{start}/{end}'.format(start=epoch_start, end=0)
    print("test_api_measurement_post_get: testapp.get('/api/{ep}')".format(ep=endpoint))
    response = testapp.get('/api/{ep}'.format(ep=endpoint), headers=headers)
    assert response.status_code == 200, "Endpoint Tested: {page}".format(page=endpoint)
    measurement_found_first = False
    measurement_found_second = False
    for each_set in json.loads(response.text)['measurements']:
        if each_set['value'] == measurements_random[0]:
            measurement_found_first = True
        if each_set['value'] == measurements_random[1]:
            measurement_found_second = True
    assert measurement_found_first and measurement_found_second, "Unexpected HTTP Response: \n{body}".format(
        body=response.body)

    # Read past stored measurements
    endpoint = 'measurements/past/testuniqueid/C/0/5'.format()
    print("test_api_measurement_post_get: testapp.get('/api/{ep}')".format(ep=endpoint))
    response = testapp.get('/api/{ep}'.format(ep=endpoint), headers=headers)
    assert response.status_code == 200, "Endpoint Tested: {page}".format(page=endpoint)
    measurement_found_first = False
    measurement_found_second = False
    for each_set in json.loads(response.text)['measurements']:
        if each_set['value'] == measurements_random[0]:
            measurement_found_first = True
        if each_set['value'] == measurements_random[1]:
            measurement_found_second = True
    assert measurement_found_first and measurement_found_second, "Unexpected HTTP Response: \n{body}".format(
        body=response.body)

    # Use historical stored measurement with SUM function
    endpoint = 'measurements/historical_function/testuniqueid/C/0/{start}/{end}/SUM'.format(
        start=epoch_start, end=epoch_end)
    print("test_api_measurement_post_get: testapp.get('/api/{ep}')".format(ep=endpoint))
    response = testapp.get('/api/{ep}'.format(ep=endpoint), headers=headers)
    assert response.status_code == 200, "Endpoint Tested: {page}".format(page=endpoint)
    assert measurements_sum == json.loads(response.text)['value'], "Unexpected HTTP Response: \n{body}".format(
        body=response.body)

    # Use historical stored measurement with SUM function (epoch_end = 0)
    endpoint = 'measurements/historical_function/testuniqueid/C/0/{start}/{end}/SUM'.format(
        start=epoch_start, end=0)
    print("test_api_measurement_post_get: testapp.get('/api/{ep}')".format(ep=endpoint))
    response = testapp.get('/api/{ep}'.format(ep=endpoint), headers=headers)
    assert response.status_code == 200, "Endpoint Tested: {page}".format(page=endpoint)
    assert measurements_sum == json.loads(response.text)['value'], "Unexpected HTTP Response: \n{body}".format(
        body=response.body)


@mock.patch('mycodo.mycodo_flask.routes_authentication.login_log')
def test_api_with_guest_apikey_in_header_403_forbidden(_, testapp):
    """ Verifies behavior of these API endpoints with an apikey in the header """
    print("\nTest: test_api_with_guest_apikey_in_header_403_forbidden")

    # Test all endpoints
    for index, route in enumerate(api_endpoints):
        print("test_api_with_guest_apikey_in_header_403_forbidden: Test Route ({}/{}): testapp.get('/api/{}')".format(
            index + 1, len(api_endpoints), route[0]))
        response = testapp.get(
            '/api/{add}'.format(add=route[0]),
            headers={
                'Accept': 'application/vnd.mycodo.v1+json',
                'X-API-KEY': base64.b64encode(b'secret_guest_api_key')
            },
            expect_errors=True
        ).maybe_follow()
        assert response.status_code == 403, "Endpoint Tested: {page}".format(page=route[0])


def test_api_when_not_logged_in(testapp):
    """
    Verifies behavior of these API endpoints when not logged in.
    All API endpoint requests should return 401 (unauthorized).
    """
    print("\nTest: test_api_when_not_logged_in")
    routes = [
        'choices/controllers',
        'choices/inputs/measurements',
        'choices/maths/measurements',
        'choices/outputs/devices',
        'choices/outputs/measurements',
        'choices/pids/measurements',
        'settings/device_measurements',
        'settings/inputs',
        'settings/maths',
        'settings/measurements',
        'settings/outputs',
        'settings/pids',
        'settings/triggers',
        'settings/units',
        'settings/users'
    ]
    for index, route in enumerate(routes):
        print("test_api_when_not_logged_in: Test Route ({}/{}): testapp.get('/api/{}').maybe_follow()".format(
            index + 1, len(routes), route))
        response = testapp.get(
            '/api/{add}'.format(add=route),
            headers={'Accept': 'application/vnd.mycodo.v1+json'},
            expect_errors=True).maybe_follow()
        assert response.status_code == 401, "Response Status Failure: {}".format('/api/{add}'.format(add=route))


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
        ('input', '<!-- Route: /input -->'),
        ('export', '<!-- Route: /export -->'),
        ('forgot_password', '<!-- Route: /forgot_password -->'),
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
        ('reset_password', '<!-- Route: /reset_password -->'),
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
def test_add_all_input_devices_logged_in_as_admin(_, testapp):
    """ Verifies adding all inputs as a logged in admin user """
    print("\nTest: test_add_all_input_devices_logged_in_as_admin")
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
        print("test_add_all_input_devices_logged_in_as_admin: Adding, saving, and deleting Input ({}/{}): {}".format(
            index + 1, len(choices_input), each_input))
        response = add_data(testapp, input_type=each_input)

        # Verify success message flashed
        assert "{} Input with ID".format(choice_name) in response
        assert "successfully added" in response

        # Verify data was entered into the database
        input_count += 1
        assert Input.query.count() == input_count, "Number of Inputs doesn't match: In DB {}, Should be: {}".format(
            Input.query.count(), input_count)

        input_dev = Input.query.filter(Input.id == input_count).first()
        assert choice_name == input_dev.device, "Input name doesn't match: {}".format(choice_name)

        # Save input
        response = save_data(testapp, 'input', device_dev=input_dev)
        assert "Success: Modify Input" in response

        # Delete input (speeds up further input addition checking)
        response = delete_data(testapp, 'input', device_dev=input_dev)
        assert "Delete input with ID: {}".format(input_dev.unique_id) in response
        input_count -= 1


@mock.patch('mycodo.mycodo_flask.routes_authentication.login_log')
def test_add_all_output_devices_logged_in_as_admin(_, testapp):
    """ Verifies adding all outputs as a logged in admin user """
    print("\nTest: test_add_all_output_devices_logged_in_as_admin")
    login_user(testapp, 'admin', '53CR3t_p4zZW0rD')

    # Add All Inputs
    output_count = 0

    dict_outputs = parse_output_information()
    list_outputs_sorted = generate_form_output_list(dict_outputs)

    choices_output = []
    for each_output in list_outputs_sorted:
        if 'interfaces' not in dict_outputs[each_output]:
            choices_output.append('{inp},'.format(inp=each_output))
        else:
            for each_interface in dict_outputs[each_output]['interfaces']:
                choices_output.append('{inp},{int}'.format(inp=each_output, int=each_interface))

    for index, each_output in enumerate(choices_output):
        print("test_add_all_output_devices_logged_in_as_admin: Adding, saving, and deleting Output ({}/{}): {}".format(
            index + 1, len(choices_output), each_output))
        response = add_output(testapp, output_type=each_output)
        # Verify success message flashed
        assert "with ID 1 successfully added" in response

        # Verify data was entered into the database
        output_count += 1
        assert Output.query.count() == output_count, "Number of Outputs doesn't match: In DB {}, Should be: {}".format(
            Output.query.count(), output_count)

        output = Output.query.filter(Output.id == output_count).first()

        # Save output
        response = save_data(testapp, 'output', device_dev=output)
        assert "Success: Modify Output" in response

        # Delete output (speeds up further output addition checking)
        response = delete_data(testapp, 'output', device_dev=output)
        assert "Success: Delete output with ID: {}".format(output.unique_id) in response
        output_count -= 1


@mock.patch('mycodo.mycodo_flask.routes_authentication.login_log')
def test_add_all_function_devices_logged_in_as_admin(_, testapp):
    """ Verifies adding all functions as a logged in admin user """
    print("\nTest: test_add_all_function_devices_logged_in_as_admin")
    login_user(testapp, 'admin', '53CR3t_p4zZW0rD')

    # Add All Custom Functions
    function_count = 0
    choices_function = choices_custom_functions()

    for index, each_function in enumerate(choices_function):
        choice_name = each_function["item"]
        print("test_add_all_function_devices_logged_in_as_admin: Adding, saving, and deleting Function ({}/{}): {}".format(
            index + 1, len(choices_function), each_function["value"]))
        response = add_function(testapp, function_type=each_function["value"])

        # Verify success message flashed
        assert "{} Function with ID".format(choice_name) in response
        assert "Success: Add Function" in response

        # Verify data was entered into the database
        function_count += 1
        assert CustomController.query.count() == function_count, "Number of Functions doesn't match: In DB {}, Should be: {}".format(
            CustomController.query.count(), function_count)

        function_dev = CustomController.query.filter(CustomController.id == function_count).first()
        assert each_function["value"] == function_dev.device, "Function name doesn't match: {}".format(choice_name)

        # Save function
        response = save_data(testapp, 'function', device_dev=function_dev)
        assert "Success: Modify Controller" in response

        # Delete function (speeds up further function addition checking)
        response = delete_data(testapp, 'function', device_dev=function_dev)
        assert "Delete custom_controller with ID: {}".format(function_dev.unique_id) in response
        function_count -= 1


# ---------------------------
#   Tests Logged in as Guest
# ---------------------------
@mock.patch('mycodo.mycodo_flask.routes_authentication.login_log')
def test_routes_logged_in_as_guest(_, testapp):
    """ Verifies behavior of these endpoints for a logged in guest user """
    print("\nTest: test_routes_logged_in_as_guest")

    print("test_routes_logged_in_as_guest: login_user(testapp, 'guest', '53CR3t_p4zZW0rD')")
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


def add_data(testapp, input_type='RPi'):
    """ Go to the data page and create input """
    form = testapp.get('/input').maybe_follow().forms['new_input_form']
    form.select(name='input_type', value=input_type)
    response = form.submit(name='input_add', value='Add').maybe_follow()
    # response.showbrowser()
    return response


def add_output(testapp, output_type='wired'):
    """ Go to the data page and create output """
    form = testapp.get('/output').maybe_follow().forms['new_output_form']
    form.set(name='output_quantity', value=1)
    form.select(name='output_type', value=output_type)
    response = form.submit(name='output_add', value='Add').maybe_follow()
    # response.showbrowser()
    return response


def add_function(testapp, function_type=''):
    """ Go to the data page and create input """
    form = testapp.get('/function').maybe_follow().forms['new_function_form']
    form.select(name='function_type', value=function_type)
    response = form.submit(name='func_add', value='Add').maybe_follow()
    # response.showbrowser()
    return response


def delete_data(testapp, data_type, device_dev=None):
    """ Go to the data page and delete input/output/function """
    response = None
    if data_type == 'input':
        form = testapp.get('/input').maybe_follow().forms['mod_input_form']
        form['input_id'].force_value(device_dev.unique_id)
        response = form.submit(name='input_delete', value='Delete').maybe_follow()
    elif data_type == 'output':
        form = testapp.get('/output').maybe_follow().forms['mod_output_form']
        form['output_id'].force_value(device_dev.unique_id)
        response = form.submit(name='delete', value='Delete').maybe_follow()
    elif data_type == 'function':
        form = testapp.get('/function').maybe_follow().forms['mod_function_form']
        form['function_id'].force_value(device_dev.unique_id)
        response = form.submit(name='delete_controller', value='Delete').maybe_follow()
    # response.showbrowser()
    return response


def save_data(testapp, data_type, device_dev=None):
    """ Go to the page and save input/output/function """
    response = None
    if data_type == 'input':
        form = testapp.get('/input').maybe_follow().forms['mod_input_form']
        form['input_id'].force_value(device_dev.unique_id)
        response = form.submit(name='input_mod', value='Save').maybe_follow()
    elif data_type == 'output':
        form = testapp.get('/output').maybe_follow().forms['mod_output_form']
        form['output_id'].force_value(device_dev.unique_id)
        response = form.submit(name='save', value='Save').maybe_follow()
    elif data_type == 'function':
        form = testapp.get('/function').maybe_follow().forms['mod_function_form']
        form['function_id'].force_value(device_dev.unique_id)
        response = form.submit(name='save_controller', value='Save').maybe_follow()
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
        'System Information',
        'Upgrade'
    ]
    assert all(
        x in response for x in navbar_strings), "Not all navbar strings found at '/' endpoint. Found: {body}".format(
        body=response.body)
