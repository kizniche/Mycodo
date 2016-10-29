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


def test_daemon_active_for_non_logged_in_user(testapp):
    """ Verifies behavior of this endpoint for non-logged in users """
    redirects_to_login_page(app=testapp, endpoint='/daemon_active')


def test_gpio_state_for_non_logged_in_user(testapp):
    """ Verifies behavior of this endpoint for non-logged in users """
    redirects_to_login_page(app=testapp, endpoint='/gpiostate')


def test_systemctl_for_non_logged_in_user(testapp):
    """ Verifies behavior of this endpoint for non-logged in users """
    redirects_to_login_page(app=testapp, endpoint='/systemctl')


def test_video_feed_for_non_logged_in_user(testapp):
    """ Verifies behavior of this endpoint for non-logged in users """
    redirects_to_login_page(app=testapp, endpoint='/video_feed')


def test_page_live_for_non_logged_in_user(testapp):
    """ Verifies behavior of this endpoint for non-logged in users """
    redirects_to_login_page(app=testapp, endpoint='/live')


def test_page_graph_for_non_logged_in_user(testapp):
    """ Verifies behavior of this endpoint for non-logged in users """
    redirects_to_login_page(app=testapp, endpoint='/graph')


def test_page_graph_async_for_non_logged_in_user(testapp):
    """ Verifies behavior of this endpoint for non-logged in users """
    redirects_to_login_page(app=testapp, endpoint='/graph-async')


def test_page_sensor_for_non_logged_in_user(testapp):
    """ Verifies behavior of this endpoint for non-logged in users """
    redirects_to_login_page(app=testapp, endpoint='/sensor')


def test_page_relay_for_non_logged_in_user(testapp):
    """ Verifies behavior of this endpoint for non-logged in users """
    redirects_to_login_page(app=testapp, endpoint='/relay')


def test_page_method_for_non_logged_in_user(testapp):
    """ Verifies behavior of this endpoint for non-logged in users """
    redirects_to_login_page(app=testapp, endpoint='/method')


def test_page_pid_for_non_logged_in_user(testapp):
    """ Verifies behavior of this endpoint for non-logged in users """
    redirects_to_login_page(app=testapp, endpoint='/pid')


def test_page_timer_for_non_logged_in_user(testapp):
    """ Verifies behavior of this endpoint for non-logged in users """
    redirects_to_login_page(app=testapp, endpoint='/timer')


def test_page_lcd_for_non_logged_in_user(testapp):
    """ Verifies behavior of this endpoint for non-logged in users """
    redirects_to_login_page(app=testapp, endpoint='/lcd')


def test_page_camera_for_non_logged_in_user(testapp):
    """ Verifies behavior of this endpoint for non-logged in users """
    redirects_to_login_page(app=testapp, endpoint='/camera')


def test_page_usage_for_non_logged_in_user(testapp):
    """ Verifies behavior of this endpoint for non-logged in users """
    redirects_to_login_page(app=testapp, endpoint='/usage')


def test_page_log_for_non_logged_in_user(testapp):
    """ Verifies behavior of this endpoint for non-logged in users """
    redirects_to_login_page(app=testapp, endpoint='/log')


def test_page_logview_for_non_logged_in_user(testapp):
    """ Verifies behavior of this endpoint for non-logged in users """
    redirects_to_login_page(app=testapp, endpoint='/logview')


def test_page_info_for_non_logged_in_user(testapp):
    """ Verifies behavior of this endpoint for non-logged in users """
    redirects_to_login_page(app=testapp, endpoint='/info')


def test_page_notes_for_non_logged_in_user(testapp):
    """ Verifies behavior of this endpoint for non-logged in users """
    redirects_to_login_page(app=testapp, endpoint='/notes')


def test_page_upgrade_for_non_logged_in_user(testapp):
    """ Verifies behavior of this endpoint for non-logged in users """
    redirects_to_login_page(app=testapp, endpoint='/upgrade')


def test_page_backup_for_non_logged_in_user(testapp):
    """ Verifies behavior of this endpoint for non-logged in users """
    redirects_to_login_page(app=testapp, endpoint='/backup')


def test_remote_admin_setup_for_non_logged_in_user(testapp):
    """ Verifies behavior of this endpoint for non-logged in users """
    redirects_to_login_page(app=testapp, endpoint='/remote/setup')


def test_settings_for_non_logged_in_user(testapp):
    """ Verifies behavior of this endpoint for non-logged in users """
    redirects_to_login_page(app=testapp, endpoint='/settings')


def test_settings_general_for_non_logged_in_user(testapp):
    """ Verifies behavior of this endpoint for non-logged in users """
    redirects_to_login_page(app=testapp, endpoint='/settings/general')


def test_settings_users_for_non_logged_in_user(testapp):
    """ Verifies behavior of this endpoint for non-logged in users """
    redirects_to_login_page(app=testapp, endpoint='/settings/users')


def test_settings_alerts_for_non_logged_in_user(testapp):
    """ Verifies behavior of this endpoint for non-logged in users """
    redirects_to_login_page(app=testapp, endpoint='/settings/alerts')


def test_settings_camera_for_non_logged_in_user(testapp):
    """ Verifies behavior of this endpoint for non-logged in users """
    redirects_to_login_page(app=testapp, endpoint='/settings/camera')


def test_sees_admin_creation_form(testapp_no_admin_user):
    """ user sees the admin creation page when the database has no admin user """
    expected_body_msg = "Mycodo was unable to find an admin user in the user database."
    assert expected_body_msg in testapp_no_admin_user.get('/').maybe_follow()


# -----------------------
#   Logged In Tests
# -----------------------
@mock.patch('mycodo.mycodo_flask.authentication.views.login_log')  # the login_log writes to a system protected file
def test_user_can_login(_, testapp, user_db):
    """ user logs in and sees a nav bar """
    # Build a user that we can login with
    norm_user = UserFactory()
    norm_user.set_password('something_secrete')
    user_db.add(norm_user)
    user_db.commit()

    # user fills out login page
    login_user(testapp, norm_user.user_name, 'something_secrete')

    # user sees the main page
    res = testapp.get('/').maybe_follow()
    assert res.status_code == 200
    # sees navbar
    assert 'Live' in res
    assert 'Graph' in res
    assert 'Sensor' in res
    assert 'Relay' in res
    assert 'Method' in res
    assert 'PID' in res
    assert 'Timer' in res
    assert 'Help' in res
    assert 'Admin' in res


@mock.patch('mycodo.mycodo_flask.authentication.views.login_log')  # the login_log writes to a system protected file
def test_does_not_see_admin_creation_form(testapp):
    """ user sees the normal login page """
    expected_body_msg = "Mycodo was unable to find an admin user in the user database."
    assert expected_body_msg not in testapp.get('/').maybe_follow()