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


def test_systemctl_for_non_logged_in_user(testapp):
    """ Verifies behavior of this endpoint for non-logged in users """
    redirects_to_login_page(app=testapp, endpoint='/systemctl')


def test_video_feed_for_non_logged_in_user(testapp):
    """ Verifies behavior of this endpoint for non-logged in users """
    redirects_to_login_page(app=testapp, endpoint='/video_feed')


def test_gpio_state_for_non_logged_in_user(testapp):
    """ Verifies behavior of this endpoint for non-logged in users """
    redirects_to_login_page(app=testapp, endpoint='/video_feed')


def test_settings_for_non_logged_in_user(testapp):
    """ Verifies behavior of this endpoint for non-logged in users """
    redirects_to_login_page(app=testapp, endpoint='/settings')


def test_settings_general_for_non_logged_in_user(testapp):
    """ Verifies behavior of this endpoint for non-logged in users """
    redirects_to_login_page(app=testapp, endpoint='/settings/general')


# -----------------------
#   Logged In Tests
# -----------------------
@mock.patch('mycodo.flaskutils.login_log')  # the login_log writes to a system protected file
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
