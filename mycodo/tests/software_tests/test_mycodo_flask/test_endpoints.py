# coding=utf-8
""" functional tests for flask endpoints """
import mock


def redirects_to_login_page(app, endpoint):
    """ helper function that verifies that we see the login page """
    response = app.get(endpoint).maybe_follow()
    assert response.status_code == 200, "Endpoint Tested: {page}".format(page=endpoint)
    assert "Mycodo Login" in response


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

