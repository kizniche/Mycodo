# coding=utf-8
"""Unit tests for login brute-force protection (login_security module).

Tests cover:
  - get_real_ip(): public IP resolution, private/loopback skipping
  - ip_failed_login(): tracker increments and ban triggering
  - ip_is_banned(): ban detection, expiry, and tracker pruning
"""
import time
import unittest
from unittest.mock import MagicMock

from mycodo.mycodo_flask.login_security import (
    _ip_fail_tracker,
    _ip_fail_tracker_lock,
    get_real_ip,
    ip_failed_login,
    ip_is_banned,
)

# Use small values so tests run fast without patching time
_ATTEMPTS = 2
_BAN_SECS = 2


def _req(remote_addr='1.2.3.4', forwarded_for=None):
    """Build a minimal mock request object."""
    req = MagicMock()
    env = {'REMOTE_ADDR': remote_addr}
    if forwarded_for is not None:
        env['HTTP_X_FORWARDED_FOR'] = forwarded_for
    req.environ = env
    return req


def _clear_tracker():
    with _ip_fail_tracker_lock:
        _ip_fail_tracker.clear()


class TestGetRealIp(unittest.TestCase):

    def test_public_remote_addr(self):
        self.assertEqual(get_real_ip(_req('8.8.8.8')), '8.8.8.8')

    def test_loopback_returns_none(self):
        self.assertIsNone(get_real_ip(_req('127.0.0.1')))

    def test_private_class_a_returns_none(self):
        self.assertIsNone(get_real_ip(_req('10.0.0.1')))

    def test_private_class_b_returns_none(self):
        self.assertIsNone(get_real_ip(_req('172.16.0.1')))

    def test_private_class_c_returns_none(self):
        self.assertIsNone(get_real_ip(_req('192.168.1.50')))

    def test_forwarded_for_leftmost_public_chosen(self):
        """Leftmost public IP in X-Forwarded-For is the original client."""
        req = _req('10.0.0.1', forwarded_for='8.8.8.8, 10.0.0.2')
        self.assertEqual(get_real_ip(req), '8.8.8.8')

    def test_forwarded_for_skips_private_ips(self):
        req = _req('10.0.0.1', forwarded_for='192.168.1.1, 172.16.0.5, 1.1.1.1')
        self.assertEqual(get_real_ip(req), '1.1.1.1')

    def test_all_private_chain_returns_none(self):
        req = _req('10.0.0.1', forwarded_for='192.168.1.1, 172.31.255.255')
        self.assertIsNone(get_real_ip(req))

    def test_malformed_entry_in_chain_skipped(self):
        req = _req('10.0.0.1', forwarded_for='not-an-ip, 1.1.1.1')
        self.assertEqual(get_real_ip(req), '1.1.1.1')

    def test_ipv6_loopback_returns_none(self):
        self.assertIsNone(get_real_ip(_req('::1')))

    def test_ipv6_public(self):
        # 2607:f8b0:: is Google's IPv6 range — genuinely public
        self.assertEqual(get_real_ip(_req('2607:f8b0::1')), '2607:f8b0::1')


class TestIpFailedLogin(unittest.TestCase):

    def setUp(self):
        _clear_tracker()

    def tearDown(self):
        _clear_tracker()

    def test_none_ip_is_noop(self):
        ip_failed_login(None, _ATTEMPTS, _BAN_SECS)
        self.assertEqual(len(_ip_fail_tracker), 0)

    def test_increments_count(self):
        ip_failed_login('8.8.8.8', _ATTEMPTS, _BAN_SECS)
        self.assertEqual(_ip_fail_tracker['8.8.8.8']['count'], 1)

    def test_triggers_ban_at_threshold(self):
        ip = '8.8.4.4'
        for _ in range(_ATTEMPTS):
            ip_failed_login(ip, _ATTEMPTS, _BAN_SECS)
        entry = _ip_fail_tracker[ip]
        self.assertGreater(entry['ban_time'], 0)
        self.assertEqual(entry['count'], 0)  # reset after ban

    def test_does_not_ban_before_threshold(self):
        ip = '1.1.1.1'
        ip_failed_login(ip, _ATTEMPTS, _BAN_SECS)
        self.assertEqual(_ip_fail_tracker[ip]['ban_time'], 0)

    def test_different_ips_tracked_independently(self):
        ip_a, ip_b = '9.9.9.9', '149.112.112.112'
        ip_failed_login(ip_a, _ATTEMPTS, _BAN_SECS)          # 1 failure only
        for _ in range(_ATTEMPTS):
            ip_failed_login(ip_b, _ATTEMPTS, _BAN_SECS)       # triggers ban
        self.assertEqual(_ip_fail_tracker[ip_a]['ban_time'], 0)
        self.assertGreater(_ip_fail_tracker[ip_b]['ban_time'], 0)


class TestIpIsBanned(unittest.TestCase):

    def setUp(self):
        _clear_tracker()

    def tearDown(self):
        _clear_tracker()

    def test_none_ip_not_banned(self):
        banned, elapsed = ip_is_banned(None, _BAN_SECS)
        self.assertFalse(banned)
        self.assertEqual(elapsed, 0)

    def test_unknown_ip_not_banned(self):
        banned, _ = ip_is_banned('8.8.8.8', _BAN_SECS)
        self.assertFalse(banned)

    def test_banned_ip_detected(self):
        ip = '8.8.4.4'
        for _ in range(_ATTEMPTS):
            ip_failed_login(ip, _ATTEMPTS, _BAN_SECS)
        banned, elapsed = ip_is_banned(ip, _BAN_SECS)
        self.assertTrue(banned)
        self.assertGreaterEqual(elapsed, 0)

    def test_expired_ban_not_detected_and_pruned(self):
        ip = '1.1.1.1'
        with _ip_fail_tracker_lock:
            _ip_fail_tracker[ip] = {
                'count': 0,
                'ban_time': time.time() - (_BAN_SECS + 1),
            }
        banned, _ = ip_is_banned(ip, _BAN_SECS)
        self.assertFalse(banned)
        self.assertNotIn(ip, _ip_fail_tracker)

    def test_ban_survives_across_independent_calls(self):
        """IP ban must persist even when checked from a different context."""
        ip = '9.9.9.9'
        for _ in range(_ATTEMPTS):
            ip_failed_login(ip, _ATTEMPTS, _BAN_SECS)
        # Simulate a second request (different session / cleared cookies)
        banned, _ = ip_is_banned(ip, _BAN_SECS)
        self.assertTrue(banned)


if __name__ == '__main__':
    unittest.main()




