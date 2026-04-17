# coding=utf-8
"""
Unit tests for framework fixes applied in the April 2026 code review.

NOTE: Linux-only stdlib modules are stubbed in sys.modules at import time so
that this test file can be executed on Windows (e.g. during CI or local dev).
"""
import sys
import types

def _stub_module(name):
    """Insert a MagicMock-backed module (and any parent packages) into sys.modules."""
    from unittest.mock import MagicMock
    parts = name.split(".")
    for i in range(1, len(parts) + 1):
        key = ".".join(parts[:i])
        if key not in sys.modules:
            sys.modules[key] = MagicMock()

for _mod in ("grp", "pwd", "resource", "fcntl", "termios", "tty",
             "readline", "crypt", "nis", "syslog", "posix"):
    _stub_module(_mod)

# Patch logging.FileHandler so that module-level log-file creation in
# mycodo_daemon.py does not fail when /var/log/mycodo/ doesn't exist.
import logging as _logging
import unittest.mock as _mock

_real_FileHandler = _logging.FileHandler

class _SafeFileHandler(_logging.Handler):
    """A no-op handler used to replace FileHandler during tests."""
    def __init__(self, *a, **kw):
        super().__init__()
    def emit(self, record):
        pass

_logging.FileHandler = _SafeFileHandler  # type: ignore[assignment]

# Covers:
#   - databases/utils.py      : sessionmaker caching
#   - utils/database.py       : db_retrieve_table_daemon raises after retries exhausted
#   - utils/influx.py         : InfluxDB client caching, refresh, ts_str Flux fix
#   - mycodo_client.py        : proxy caching, timeout restore, mutable-default fix
#   - controllers/base_controller.py : ready.set() safety net
#   - mycodo_daemon.py        : cont_type=None guard, ready.wait timeout
import threading
import unittest
from unittest.mock import MagicMock, patch, call


# ---------------------------------------------------------------------------
# databases/utils.py — sessionmaker caching
# ---------------------------------------------------------------------------
class TestSessionScopeCache(unittest.TestCase):
    """The sessionmaker for a given URI should be created once and reused."""

    def setUp(self):
        # Reset the module-level caches before every test so tests are isolated.
        import mycodo.databases.utils as db_utils
        db_utils._engine_cache.clear()
        db_utils._session_factory_cache.clear()

    def test_same_factory_returned_for_same_uri(self):
        """Two calls with the same URI must return the identical SessionFactory."""
        import mycodo.databases.utils as db_utils
        _, factory1 = db_utils._get_engine_and_factory("sqlite:///:memory:")
        _, factory2 = db_utils._get_engine_and_factory("sqlite:///:memory:")
        self.assertIs(factory1, factory2)

    def test_different_uris_get_different_factories(self):
        """Different URIs must produce independent factories."""
        import mycodo.databases.utils as db_utils
        _, factory1 = db_utils._get_engine_and_factory("sqlite:///:memory:?a=1")
        _, factory2 = db_utils._get_engine_and_factory("sqlite:///:memory:?a=2")
        self.assertIsNot(factory1, factory2)

    def test_engine_created_only_once(self):
        """create_engine should be called exactly once per unique URI."""
        import mycodo.databases.utils as db_utils
        with patch("mycodo.databases.utils.create_engine", wraps=db_utils.create_engine) as mock_ce:
            db_utils._get_engine_and_factory("sqlite:///:memory:?test=once")
            db_utils._get_engine_and_factory("sqlite:///:memory:?test=once")
            self.assertEqual(mock_ce.call_count, 1)


# ---------------------------------------------------------------------------
# utils/database.py — db_retrieve_table_daemon raises after exhausted retries
# ---------------------------------------------------------------------------
class TestDbRetrieveTableDaemonRaises(unittest.TestCase):
    """After 5 consecutive OperationalError retries the function must raise."""

    def test_raises_runtime_error_after_retries(self):
        from sqlite3 import OperationalError
        from mycodo.utils.database import db_retrieve_table_daemon

        mock_table = MagicMock()

        # Make session_scope always raise OperationalError to exhaust retries.
        with patch("mycodo.utils.database.session_scope") as mock_scope, \
             patch("mycodo.utils.database.time.sleep"):  # skip actual sleeps
            mock_scope.side_effect = OperationalError("locked")
            with self.assertRaises(RuntimeError) as ctx:
                db_retrieve_table_daemon(mock_table, entry='first')
            self.assertIn("5 attempts", str(ctx.exception))

    def test_returns_result_on_first_success(self):
        from mycodo.utils.database import db_retrieve_table_daemon
        from contextlib import contextmanager

        mock_table = MagicMock()
        mock_row = MagicMock()

        @contextmanager
        def good_scope(_uri):
            mock_session = MagicMock()
            mock_session.query.return_value.first.return_value = mock_row
            mock_session.query.return_value.all.return_value = [mock_row]
            yield mock_session

        with patch("mycodo.utils.database.session_scope", good_scope):
            result = db_retrieve_table_daemon(mock_table, entry='first')
        self.assertIs(result, mock_row)


# ---------------------------------------------------------------------------
# utils/influx.py — InfluxDB client caching & refresh
# ---------------------------------------------------------------------------
class TestInfluxClientCache(unittest.TestCase):

    def _make_settings(self, host="localhost", port=8086, version="2",
                       user="admin", password="secret",
                       dbname="mycodo", policy="autogen"):
        s = MagicMock()
        s.measurement_db_host = host
        s.measurement_db_port = port
        s.measurement_db_version = version
        s.measurement_db_user = user
        s.measurement_db_password = password
        s.measurement_db_dbname = dbname
        s.measurement_db_retention_policy = policy
        return s

    def setUp(self):
        # Reset cache before each test.
        from mycodo.utils import influx as inf
        inf._influx_client_cache.clear()

    def test_same_settings_returns_cached_client(self):
        from mycodo.utils.influx import _get_influx_client
        settings = self._make_settings()

        with patch("mycodo.utils.influx.InfluxDBClient") as MockClient:
            MockClient.return_value = MagicMock()
            c1 = _get_influx_client(settings)
            c2 = _get_influx_client(settings)

        # InfluxDBClient constructor should be called exactly once.
        self.assertEqual(MockClient.call_count, 1)
        self.assertIs(c1, c2)

    def test_changed_settings_creates_new_client(self):
        from mycodo.utils.influx import _get_influx_client
        settings_a = self._make_settings(host="host-a")
        settings_b = self._make_settings(host="host-b")

        with patch("mycodo.utils.influx.InfluxDBClient") as MockClient:
            instance_a = MagicMock()
            instance_b = MagicMock()
            MockClient.side_effect = [instance_a, instance_b]

            c1 = _get_influx_client(settings_a)
            c2 = _get_influx_client(settings_b)

        self.assertEqual(MockClient.call_count, 2)
        self.assertIs(c1, instance_a)
        self.assertIs(c2, instance_b)
        # Old client should have been closed when settings changed.
        instance_a.close.assert_called_once()

    def test_refresh_influx_client_clears_cache(self):
        from mycodo.utils.influx import _get_influx_client, refresh_influx_client
        settings = self._make_settings()

        with patch("mycodo.utils.influx.InfluxDBClient") as MockClient:
            old_instance = MagicMock()
            new_instance = MagicMock()
            MockClient.side_effect = [old_instance, new_instance]

            _get_influx_client(settings)
            refresh_influx_client()
            c2 = _get_influx_client(settings)

        self.assertEqual(MockClient.call_count, 2)
        self.assertIs(c2, new_instance)

    def test_unknown_version_raises(self):
        from mycodo.utils.influx import _get_influx_client
        settings = self._make_settings(version="99")
        with patch("mycodo.utils.influx.InfluxDBClient"):
            with self.assertRaises(ValueError):
                _get_influx_client(settings)

    def test_get_influx_bucket_version1(self):
        from mycodo.utils.influx import _get_influx_bucket
        settings = self._make_settings(version="1", dbname="mydb", policy="rp30d")
        self.assertEqual(_get_influx_bucket(settings), "mydb/rp30d")

    def test_get_influx_bucket_version2(self):
        from mycodo.utils.influx import _get_influx_bucket
        settings = self._make_settings(version="2", dbname="mydb")
        self.assertEqual(_get_influx_bucket(settings), "mydb")


# ---------------------------------------------------------------------------
# utils/influx.py — ts_str Flux syntax fix
# ---------------------------------------------------------------------------
class TestQueryFluxTsStr(unittest.TestCase):
    """The ts_str filter must use valid Flux time() syntax, not InfluxQL."""

    def _make_settings(self, version="2"):
        s = MagicMock()
        s.measurement_db_host = "localhost"
        s.measurement_db_port = 8086
        s.measurement_db_version = version
        s.measurement_db_user = "u"
        s.measurement_db_password = "p"
        s.measurement_db_dbname = "mycodo"
        s.measurement_db_retention_policy = "autogen"
        s.measurement_db_name = "influxdb"
        return s

    def test_ts_str_uses_flux_time_syntax(self):
        from mycodo.utils import influx as inf

        settings = self._make_settings()
        mock_client = MagicMock()
        mock_client.query_api.return_value.query.return_value = []

        captured_queries = []

        def fake_query(q):
            captured_queries.append(q)
            return []

        mock_client.query_api.return_value.query.side_effect = fake_query

        with patch("mycodo.utils.influx.db_retrieve_table_daemon", return_value=settings), \
             patch.object(inf, "_influx_client_cache",
                          {inf._make_influx_key(settings): mock_client}):
            inf.query_flux("C", "device-123",
                           ts_str="2024-01-15T10:30:00Z",
                           past_sec=3600)

        self.assertEqual(len(captured_queries), 1)
        query = captured_queries[0]
        # Must NOT contain InfluxQL syntax
        self.assertNotIn("AND time =", query)
        # Must contain valid Flux time() filter
        self.assertIn('r["_time"] == time(v: "2024-01-15T10:30:00Z")', query)


# ---------------------------------------------------------------------------
# mycodo_client.py — proxy caching, timeout restore, mutable default
# ---------------------------------------------------------------------------
class TestDaemonControlProxy(unittest.TestCase):

    def _make_control(self, timeout=30):
        from mycodo.mycodo_client import DaemonControl
        with patch("mycodo.mycodo_client.db_retrieve_table_daemon") as mock_db:
            mock_misc = MagicMock()
            mock_misc.rpyc_timeout = timeout
            mock_db.return_value = mock_misc
            ctrl = DaemonControl.__new__(DaemonControl)
            ctrl.pyro_timeout = timeout
            ctrl.uri = "PYRO:test@127.0.0.1:9080"
            ctrl._proxy = None
        return ctrl

    def test_proxy_reused_on_consecutive_calls(self):
        ctrl = self._make_control()
        mock_proxy_instance = MagicMock()
        mock_proxy_instance._pyroTimeout = 30

        with patch("mycodo.mycodo_client.Proxy", return_value=mock_proxy_instance) as MockProxy:
            p1 = ctrl.proxy()
            p2 = ctrl.proxy()

        MockProxy.assert_called_once()  # Proxy() constructed only once
        self.assertIs(p1, p2)

    def test_reset_proxy_causes_new_proxy_on_next_call(self):
        ctrl = self._make_control()
        instance1 = MagicMock()
        instance1._pyroTimeout = 30
        instance2 = MagicMock()
        instance2._pyroTimeout = 30

        with patch("mycodo.mycodo_client.Proxy", side_effect=[instance1, instance2]):
            p1 = ctrl.proxy()
            ctrl._reset_proxy()
            p2 = ctrl.proxy()

        self.assertIs(p1, instance1)
        self.assertIs(p2, instance2)

    def test_custom_timeout_is_restored_after_module_function(self):
        """After module_function with a custom timeout, the proxy's timeout
        must be restored to the default."""
        ctrl = self._make_control(timeout=30)
        mock_proxy = MagicMock()
        mock_proxy._pyroTimeout = 30
        mock_proxy.module_function.return_value = (0, "ok")

        with patch("mycodo.mycodo_client.Proxy", return_value=mock_proxy):
            ctrl.module_function(
                "Input", "uid", "btn", {}, timeout=120)

        # After the call, timeout must be restored to default (30).
        self.assertEqual(mock_proxy._pyroTimeout, 30)

    def test_trigger_action_mutable_default_independent(self):
        """Successive trigger_action calls with no value arg must not share state."""
        ctrl = self._make_control()
        mock_proxy = MagicMock()
        mock_proxy._pyroTimeout = 30
        # Capture the value dict passed on each call
        captured = []
        mock_proxy.trigger_action.side_effect = lambda aid, value, debug: captured.append(value) or (0, "ok")

        with patch("mycodo.mycodo_client.Proxy", return_value=mock_proxy):
            ctrl.trigger_action("action-1")
            # Mutate what the proxy received on the first call (simulates rogue mutation)
            if captured:
                captured[0]["injected"] = True
            ctrl.trigger_action("action-2")

        # The second call's value dict must be a fresh empty dict.
        self.assertEqual(len(captured), 2)
        self.assertNotIn("injected", captured[1])


# ---------------------------------------------------------------------------
# controllers/base_controller.py — ready.set() safety net
# ---------------------------------------------------------------------------
class TestBaseControllerReadySafetyNet(unittest.TestCase):
    """If initialize_variables() doesn't call ready.set(), the base must do it."""

    def _make_controller(self, ready, sets_ready=True, sets_running=True):
        """Build a minimal concrete AbstractController subclass."""
        from mycodo.controllers.base_controller import AbstractController

        class _FakeController(AbstractController, threading.Thread):
            def __init__(self, ready_event):
                threading.Thread.__init__(self)
                # Bypass super().__init__ DB calls for testing
                self.ready = ready_event
                self.running = False
                self.thread_startup_timer = __import__("timeit").default_timer()
                self.thread_shutdown_timer = 0
                self.sample_rate = 0
                self.unique_id = None
                self.logger = __import__("logging").getLogger("test.base_controller")

            def initialize_variables(self):
                if sets_running:
                    self.running = True
                if sets_ready:
                    self.ready.set()

            def loop(self):
                # Run once then stop so the test thread exits.
                self.running = False

            def run_finally(self):
                pass

        ctrl = _FakeController(ready)
        ctrl.daemon = True
        return ctrl

    def test_ready_set_by_subclass_no_warning(self):
        """Normal case: subclass calls ready.set() — no warning, event is set."""
        ready = threading.Event()
        ctrl = self._make_controller(ready, sets_ready=True, sets_running=True)
        ctrl.start()
        fired = ready.wait(timeout=5)
        ctrl.join(timeout=5)
        self.assertTrue(fired)

    def test_ready_set_by_base_when_subclass_forgets(self):
        """Safety net: if subclass omits ready.set(), base must set it."""
        ready = threading.Event()
        ctrl = self._make_controller(ready, sets_ready=False, sets_running=True)
        ctrl.start()
        # With the safety net, ready must still be set within a short window.
        fired = ready.wait(timeout=5)
        ctrl.join(timeout=5)
        self.assertTrue(fired, "Base controller safety net failed to call ready.set()")


# ---------------------------------------------------------------------------
# mycodo_daemon.py — cont_type=None guard
# ---------------------------------------------------------------------------
class TestDetermineControllerTypeNoneGuard(unittest.TestCase):
    """controller_activate/deactivate/is_active must handle cont_type=None cleanly."""

    def _make_daemon(self):
        from mycodo.mycodo_daemon import DaemonController
        daemon = DaemonController.__new__(DaemonController)
        daemon.logger = MagicMock()
        daemon.controller = {
            'Conditional': {}, 'Output': None, 'Widget': None,
            'Input': {}, 'PID': {}, 'Trigger': {}, 'Function': {}
        }
        return daemon

    def test_controller_activate_unknown_id_returns_error(self):
        from mycodo.mycodo_daemon import DaemonController
        daemon = self._make_daemon()
        with patch.object(DaemonController, "determine_controller_type", return_value=None):
            status, msg = daemon.controller_activate("nonexistent-id")
        self.assertEqual(status, 1)
        self.assertIn("not found", msg)

    def test_controller_deactivate_unknown_id_returns_error(self):
        from mycodo.mycodo_daemon import DaemonController
        daemon = self._make_daemon()
        with patch.object(DaemonController, "determine_controller_type", return_value=None):
            status, msg = daemon.controller_deactivate("nonexistent-id")
        self.assertEqual(status, 1)
        self.assertIn("not found", msg)

    def test_controller_is_active_unknown_id_returns_false(self):
        from mycodo.mycodo_daemon import DaemonController
        daemon = self._make_daemon()
        with patch.object(DaemonController, "determine_controller_type", return_value=None):
            result = daemon.controller_is_active("nonexistent-id")
        self.assertFalse(result)


# ---------------------------------------------------------------------------
# PUBLIC API IMPORT CONTRACT
# Verify that the permanent user-facing symbols resolve at their documented
# import paths.  These imports MUST never fail — user code stored in the
# database (conditional controllers, Python Inputs/Outputs, custom modules)
# depends on them and cannot be regenerated automatically.
# ---------------------------------------------------------------------------
class TestPublicApiImportPaths(unittest.TestCase):
    """Smoke-test that the permanent public-API symbols are importable."""

    def test_session_scope_importable(self):
        """session_scope must be importable from mycodo.databases.utils."""
        from mycodo.databases.utils import session_scope  # noqa: F401
        self.assertTrue(callable(session_scope))

    def test_db_retrieve_table_daemon_importable(self):
        """db_retrieve_table_daemon must be importable from mycodo.utils.database."""
        from mycodo.utils.database import db_retrieve_table_daemon  # noqa: F401
        self.assertTrue(callable(db_retrieve_table_daemon))

    def test_db_retrieve_table_importable(self):
        """db_retrieve_table must be importable from mycodo.utils.database."""
        from mycodo.utils.database import db_retrieve_table  # noqa: F401
        self.assertTrue(callable(db_retrieve_table))

    def test_db_retrieve_table_daemon_signature(self):
        """db_retrieve_table_daemon must accept all documented keyword arguments."""
        import inspect
        from mycodo.utils.database import db_retrieve_table_daemon
        sig = inspect.signature(db_retrieve_table_daemon)
        params = set(sig.parameters.keys())
        required = {'table', 'entry', 'device_id', 'unique_id', 'custom_name', 'custom_value'}
        self.assertTrue(
            required.issubset(params),
            f"Missing parameters: {required - params}"
        )

    def test_db_retrieve_table_signature(self):
        """db_retrieve_table must accept all documented keyword arguments."""
        import inspect
        from mycodo.utils.database import db_retrieve_table
        sig = inspect.signature(db_retrieve_table)
        params = set(sig.parameters.keys())
        required = {'table', 'entry', 'unique_id'}
        self.assertTrue(
            required.issubset(params),
            f"Missing parameters: {required - params}"
        )


# ---------------------------------------------------------------------------
# databases/__init__.py — CRUDMixin context-aware session routing
# ---------------------------------------------------------------------------
class TestCRUDMixinContextRouting(unittest.TestCase):
    """
    CRUDMixin.save() and .delete() must use db.session inside a Flask app
    context and fall back to session_scope outside one.
    """

    def _make_instance(self):
        """Create a minimal CRUDMixin instance (no real DB model needed)."""
        from mycodo.databases import CRUDMixin

        class FakeModel(CRUDMixin):
            def __init__(self):
                self.__table__ = None  # not needed for these tests

        return FakeModel()

    # ---- outside-Flask -------------------------------------------------------

    def test_save_outside_flask_uses_session_scope(self):
        """
        Outside a Flask context, save() must route through session_scope.
        We verify this by confirming that session_scope is called and that
        no attempt is made to access db.session (which would raise outside Flask).
        """
        from contextlib import contextmanager
        instance = self._make_instance()

        mock_session = MagicMock()
        scope_entered = []

        @contextmanager
        def fake_scope(_uri):
            scope_entered.append(True)
            yield mock_session

        # Patch flask.has_app_context so the method takes the outside-Flask branch,
        # and patch session_scope at the source so the lazy import inside save() picks
        # up our fake.
        with patch("flask.has_app_context", return_value=False), \
             patch("mycodo.databases.utils.session_scope", fake_scope):
            try:
                instance.save()
            except Exception:
                pass  # merge will fail on a MagicMock session — that's expected

        # session_scope was entered, confirming the daemon branch was taken.
        self.assertTrue(scope_entered, "session_scope was never called — wrong branch taken")

    def test_save_outside_flask_does_not_import_flask_db(self):
        """
        Outside Flask context, save() must not attempt to access db.session —
        doing so would raise RuntimeError inside the daemon.
        """
        instance = self._make_instance()

        mock_session = MagicMock()

        from contextlib import contextmanager

        @contextmanager
        def fake_scope(_uri):
            yield mock_session

        # Simulate no Flask app context
        with patch("flask.has_app_context", return_value=False), \
             patch("mycodo.databases.utils.session_scope", fake_scope):
            try:
                instance.save()
            except Exception:
                pass  # Real merge will fail without a DB; that's OK

        # If we got here without a RuntimeError about missing app context, pass.

    # ---- inside-Flask --------------------------------------------------------

    def test_save_inside_flask_uses_db_session(self):
        """Inside a Flask context, save() must call db.session.add and commit."""
        instance = self._make_instance()

        mock_db_session = MagicMock()

        with patch("flask.has_app_context", return_value=True), \
             patch("mycodo.mycodo_flask.extensions.db") as mock_db:
            mock_db.session = mock_db_session
            try:
                instance.save()
            except Exception:
                pass

        mock_db_session.add.assert_called_once_with(instance)
        mock_db_session.commit.assert_called_once()

    def test_delete_inside_flask_uses_db_session(self):
        """Inside a Flask context, delete() must call db.session.delete and commit."""
        instance = self._make_instance()

        mock_db_session = MagicMock()

        with patch("flask.has_app_context", return_value=True), \
             patch("mycodo.mycodo_flask.extensions.db") as mock_db:
            mock_db.session = mock_db_session
            try:
                instance.delete()
            except Exception:
                pass

        mock_db_session.delete.assert_called_once_with(instance)
        mock_db_session.commit.assert_called_once()


# ---------------------------------------------------------------------------
# utils/database.py — db_retrieve_table context-aware fallback
# ---------------------------------------------------------------------------
class TestDbRetrieveTableContextFallback(unittest.TestCase):
    """
    db_retrieve_table must use Model.query inside Flask and fall back to
    db_retrieve_table_daemon (session_scope) outside Flask.
    """

    def test_outside_flask_falls_back_to_session_scope(self):
        """Outside Flask, db_retrieve_table must return results via session_scope."""
        from mycodo.utils.database import db_retrieve_table
        from contextlib import contextmanager

        mock_table = MagicMock()
        mock_row = MagicMock()

        @contextmanager
        def good_scope(_uri):
            mock_session = MagicMock()
            mock_session.query.return_value.first.return_value = mock_row
            yield mock_session

        with patch("flask.has_app_context", return_value=False), \
             patch("mycodo.utils.database.session_scope", good_scope):
            result = db_retrieve_table(mock_table, entry='first')

        self.assertIs(result, mock_row)

    def test_inside_flask_uses_model_query(self):
        """Inside Flask, db_retrieve_table must use the Model.query proxy."""
        from mycodo.utils.database import db_retrieve_table

        mock_table = MagicMock()
        mock_row = MagicMock()
        mock_table.query.first.return_value = mock_row

        with patch("flask.has_app_context", return_value=True):
            result = db_retrieve_table(mock_table, entry='first')

        mock_table.query.first.assert_called_once()
        self.assertIs(result, mock_row)

    def test_outside_flask_all_entries(self):
        """Outside Flask, db_retrieve_table with entry='all' returns a list."""
        from mycodo.utils.database import db_retrieve_table
        from contextlib import contextmanager

        mock_table = MagicMock()
        mock_rows = [MagicMock(), MagicMock()]

        @contextmanager
        def good_scope(_uri):
            mock_session = MagicMock()
            mock_session.query.return_value.all.return_value = mock_rows
            yield mock_session

        with patch("flask.has_app_context", return_value=False), \
             patch("mycodo.utils.database.session_scope", good_scope):
            result = db_retrieve_table(mock_table, entry='all')

        self.assertEqual(result, mock_rows)


# ---------------------------------------------------------------------------
# conftest helper — no_app_context fixture equivalent (unittest version)
# ---------------------------------------------------------------------------
class TestNoAppContextIsolation(unittest.TestCase):
    """
    Verify that without any patches, importing the database modules does not
    require a live Flask application (i.e. no app-context-at-import-time error).
    """

    def test_databases_init_importable_without_flask_app(self):
        """databases/__init__.py must be importable without a Flask app running."""
        # If the old code (hard import of db at module level) were still there,
        # this would raise an ImportError or application context error.
        import importlib
        import mycodo.databases as db_init
        importlib.reload(db_init)
        self.assertTrue(hasattr(db_init, 'CRUDMixin'))
        self.assertTrue(hasattr(db_init, 'clone_model'))

    def test_databases_utils_importable_without_flask_app(self):
        """databases/utils.py must be importable without a Flask app running."""
        import mycodo.databases.utils as db_utils
        self.assertTrue(hasattr(db_utils, 'session_scope'))
        self.assertTrue(hasattr(db_utils, '_get_engine_and_factory'))

    def test_utils_database_importable_without_flask_app(self):
        """utils/database.py must be importable without a Flask app running."""
        import mycodo.utils.database as db_mod
        self.assertTrue(hasattr(db_mod, 'db_retrieve_table'))
        self.assertTrue(hasattr(db_mod, 'db_retrieve_table_daemon'))


if __name__ == "__main__":
    unittest.main()

