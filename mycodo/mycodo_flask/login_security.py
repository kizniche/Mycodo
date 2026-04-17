# coding=utf-8
"""Login brute-force protection helpers.

Kept in a separate module so they can be imported and unit-tested without
pulling in the full Flask application context or database models.
"""

import ipaddress
import logging
import threading
import time

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory IP-based ban tracker (resets on server restart).
# Structure: { ip_str: {'count': int, 'ban_time': float or 0} }
# ---------------------------------------------------------------------------
_ip_fail_tracker = {}
_ip_fail_tracker_lock = threading.Lock()
try:
    from mycodo.config_override import TRUSTED_PROXIES
except ImportError:
    from mycodo.config import TRUSTED_PROXIES
_trusted_proxies = set(TRUSTED_PROXIES)


def get_real_ip(request):
    """Return the first non-private, non-loopback IP from the request.

    Honors X-Forwarded-For only when REMOTE_ADDR is a trusted proxy.
    Falls back to REMOTE_ADDR. Returns None if every candidate address is
    private/loopback (to avoid banning an entire LAN).
    """
    candidates = []

    remote_addr = request.environ.get('REMOTE_ADDR', '')
    if remote_addr and remote_addr in _trusted_proxies:
        forwarded_for = request.environ.get('HTTP_X_FORWARDED_FOR', '')
        if forwarded_for:
            candidates.extend(
                addr.strip() for addr in forwarded_for.split(',') if addr.strip()
            )
    if remote_addr:
        candidates.append(remote_addr)

    for addr in candidates:
        try:
            ip = ipaddress.ip_address(addr)
            if not ip.is_loopback and not ip.is_private:
                return str(ip)
        except ValueError:
            continue

    # All addresses were private/loopback.
    if candidates:
        logger.debug(
            "get_real_ip: all candidate IPs are private/loopback (%s); "
            "IP-based ban will not be applied.", candidates
        )
    return None


def ip_failed_login(client_ip, login_attempts, login_ban_seconds):
    """Record a failed login attempt for a given IP address.

    Args:
        client_ip: Resolved public IP string, or None (no-op).
        login_attempts: Number of failures before a ban is triggered.
        login_ban_seconds: How long (seconds) the ban lasts.
    """
    if not client_ip:
        return

    with _ip_fail_tracker_lock:
        entry = _ip_fail_tracker.setdefault(
            client_ip, {'count': 0, 'ban_time': 0}
        )
        entry['count'] += 1
        if entry['count'] >= login_attempts:
            entry['ban_time'] = time.time()
            entry['count'] = 0
            logger.warning(
                "IP %s banned for %s seconds after %s failed login attempts.",
                client_ip, login_ban_seconds, login_attempts
            )


def ip_is_banned(client_ip, login_ban_seconds):
    """Return (is_banned, elapsed_seconds) for the given IP.

    Also prunes expired entries from the tracker to prevent unbounded growth.

    Args:
        client_ip: Resolved public IP string, or None.
        login_ban_seconds: Ban duration in seconds.

    Returns:
        (True, elapsed) if the IP is currently banned, (False, 0) otherwise.
    """
    if not client_ip:
        return False, 0

    now = time.time()
    with _ip_fail_tracker_lock:
        # Prune expired entries
        expired = [
            ip for ip, data in _ip_fail_tracker.items()
            if data['ban_time'] and (now - data['ban_time']) >= login_ban_seconds
        ]
        for ip in expired:
            del _ip_fail_tracker[ip]

        entry = _ip_fail_tracker.get(client_ip)
        if entry and entry['ban_time']:
            elapsed = now - entry['ban_time']
            if elapsed < login_ban_seconds:
                return True, elapsed

    return False, 0
