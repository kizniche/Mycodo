# coding=utf-8
"""Tests for settings function update utility function."""
import os
import shutil
import tempfile

import mock
import pytest
from unittest.mock import MagicMock, patch


# A minimal valid custom function module content
VALID_FUNCTION_CONTENT = b"""FUNCTION_INFORMATION = {
    'function_name_unique': 'MY_CUSTOM_FUNCTION',
    'function_name': 'My Custom Function',
}
"""

VALID_FUNCTION_UNIQUE_NAME = 'MY_CUSTOM_FUNCTION'


class MockFileStorage:
    """Mock Werkzeug FileStorage for testing file uploads."""

    def __init__(self, filename, content):
        self.filename = filename
        self._content = content

    def save(self, dst):
        with open(dst, 'wb') as f:
            f.write(self._content)


def make_del_form(controller_id):
    """Create a mock ControllerDel form (supplies controller_id)."""
    form = MagicMock()
    form.controller_id.data = controller_id
    return form


def make_mod_form(file_storage):
    """Create a mock ControllerMod form (supplies the replacement file)."""
    form = MagicMock()
    form.update_controller_file.data = file_storage
    return form


@pytest.fixture()
def custom_functions_dir():
    """Create a temporary directory to act as PATH_FUNCTIONS_CUSTOM."""
    tmp_dir = tempfile.mkdtemp()
    yield tmp_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture()
def tmp_install_dir():
    """Create a temporary directory to act as INSTALL_DIRECTORY."""
    tmp_dir = tempfile.mkdtemp()
    yield tmp_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture()
def mock_mycodo_user():
    """
    Mock pwd.getpwnam and grp.getgrnam so that looking up the 'mycodo'
    user/group resolves to the current process's UID/GID.  This lets
    os.chown succeed in CI without a real mycodo system account, while
    still exercising the full assure_path_exists / set_user_grp code path.
    """
    current_uid = os.getuid()
    current_gid = os.getgid()

    mock_pw = MagicMock()
    mock_pw.pw_uid = current_uid

    mock_gr = MagicMock()
    mock_gr.gr_gid = current_gid

    with patch('mycodo.utils.system_pi.pwd.getpwnam', return_value=mock_pw), \
            patch('mycodo.utils.system_pi.grp.getgrnam', return_value=mock_gr):
        yield


def write_existing_module(custom_functions_dir, content=None):
    """Write the existing module file to PATH_FUNCTIONS_CUSTOM so the update function can load it."""
    if content is None:
        content = VALID_FUNCTION_CONTENT
    path = os.path.join(custom_functions_dir, 'my_custom_function.py')
    with open(path, 'wb') as f:
        f.write(content)
    return path


class TestSettingsFunctionUpdate:
    """Tests for the settings_function_update utility function."""

    @mock.patch('subprocess.Popen')
    def test_update_valid_module_no_activated_functions(
            self, mock_popen, app, custom_functions_dir, tmp_install_dir,
            mock_mycodo_user):
        """A valid update with no activated functions: only frontend reload, no daemon restart."""
        from mycodo.mycodo_flask.utils.utils_settings import settings_function_update

        # Write the existing module that will be read from disk for comparison
        write_existing_module(custom_functions_dir)

        form_del = make_del_form(VALID_FUNCTION_UNIQUE_NAME)
        form = make_mod_form(MockFileStorage('my_custom_function.py', VALID_FUNCTION_CONTENT))

        with patch('mycodo.mycodo_flask.utils.utils_settings.INSTALL_DIRECTORY', tmp_install_dir), \
                patch('mycodo.mycodo_flask.utils.utils_settings.PATH_FUNCTIONS_CUSTOM', custom_functions_dir), \
                patch('mycodo.mycodo_flask.utils.utils_settings.CustomController') as mock_cc:
            mock_cc.query.filter.return_value.count.return_value = 0
            settings_function_update(form_del, form)

        # File should be written to the custom functions directory
        expected_file = os.path.join(custom_functions_dir, 'my_custom_function.py')
        assert os.path.exists(expected_file)
        with open(expected_file, 'rb') as f:
            assert b'MY_CUSTOM_FUNCTION' in f.read()

        # Only the frontend reload should have been triggered
        assert mock_popen.call_count == 1
        assert 'frontend_reload' in mock_popen.call_args[0][0]

    @mock.patch('subprocess.Popen')
    def test_update_valid_module_with_activated_function(
            self, mock_popen, app, custom_functions_dir, tmp_install_dir,
            mock_mycodo_user):
        """A valid update with at least one activated function triggers both frontend reload and daemon restart."""
        from mycodo.mycodo_flask.utils.utils_settings import settings_function_update

        write_existing_module(custom_functions_dir)

        form_del = make_del_form(VALID_FUNCTION_UNIQUE_NAME)
        form = make_mod_form(MockFileStorage('my_custom_function.py', VALID_FUNCTION_CONTENT))

        with patch('mycodo.mycodo_flask.utils.utils_settings.INSTALL_DIRECTORY', tmp_install_dir), \
                patch('mycodo.mycodo_flask.utils.utils_settings.PATH_FUNCTIONS_CUSTOM', custom_functions_dir), \
                patch('mycodo.mycodo_flask.utils.utils_settings.CustomController') as mock_cc:
            # One activated CustomController entry exists for this module
            mock_cc.query.filter.return_value.count.return_value = 1
            settings_function_update(form_del, form)

        # File should exist
        assert os.path.exists(os.path.join(custom_functions_dir, 'my_custom_function.py'))

        # Both frontend_reload and daemon_restart should have been triggered
        assert mock_popen.call_count == 2
        calls = [c[0][0] for c in mock_popen.call_args_list]
        assert any('frontend_reload' in c for c in calls)
        assert any('daemon_restart' in c for c in calls)

    @mock.patch('subprocess.Popen')
    def test_update_overwrites_existing_module(
            self, mock_popen, app, custom_functions_dir, tmp_install_dir,
            mock_mycodo_user):
        """Updating an existing module overwrites its file content."""
        from mycodo.mycodo_flask.utils.utils_settings import settings_function_update

        # Write a recognisably "old" version of the existing module
        write_existing_module(custom_functions_dir, VALID_FUNCTION_CONTENT + b'# old version\n')

        new_content = VALID_FUNCTION_CONTENT + b'# new version\n'
        form_del = make_del_form(VALID_FUNCTION_UNIQUE_NAME)
        form = make_mod_form(MockFileStorage('my_custom_function.py', new_content))

        with patch('mycodo.mycodo_flask.utils.utils_settings.INSTALL_DIRECTORY', tmp_install_dir), \
                patch('mycodo.mycodo_flask.utils.utils_settings.PATH_FUNCTIONS_CUSTOM', custom_functions_dir), \
                patch('mycodo.mycodo_flask.utils.utils_settings.CustomController') as mock_cc:
            mock_cc.query.filter.return_value.count.return_value = 0
            settings_function_update(form_del, form)

        with open(os.path.join(custom_functions_dir, 'my_custom_function.py'), 'rb') as f:
            content = f.read()
        assert b'# old version' not in content
        assert b'# new version' in content

    @mock.patch('subprocess.Popen')
    def test_update_no_file_fails(
            self, mock_popen, app, custom_functions_dir, tmp_install_dir,
            mock_mycodo_user):
        """Submitting with no file should not update or trigger any subprocess."""
        from mycodo.mycodo_flask.utils.utils_settings import settings_function_update

        write_existing_module(custom_functions_dir)
        form_del = make_del_form(VALID_FUNCTION_UNIQUE_NAME)
        form = make_mod_form(None)

        with patch('mycodo.mycodo_flask.utils.utils_settings.INSTALL_DIRECTORY', tmp_install_dir), \
                patch('mycodo.mycodo_flask.utils.utils_settings.PATH_FUNCTIONS_CUSTOM', custom_functions_dir):
            settings_function_update(form_del, form)

        mock_popen.assert_not_called()

    @mock.patch('subprocess.Popen')
    def test_update_empty_filename_fails(
            self, mock_popen, app, custom_functions_dir, tmp_install_dir,
            mock_mycodo_user):
        """Submitting with an empty filename should not update or trigger any subprocess."""
        from mycodo.mycodo_flask.utils.utils_settings import settings_function_update

        write_existing_module(custom_functions_dir)
        form_del = make_del_form(VALID_FUNCTION_UNIQUE_NAME)
        form = make_mod_form(MockFileStorage('', VALID_FUNCTION_CONTENT))

        with patch('mycodo.mycodo_flask.utils.utils_settings.INSTALL_DIRECTORY', tmp_install_dir), \
                patch('mycodo.mycodo_flask.utils.utils_settings.PATH_FUNCTIONS_CUSTOM', custom_functions_dir):
            settings_function_update(form_del, form)

        mock_popen.assert_not_called()

    @mock.patch('subprocess.Popen')
    def test_update_different_filename_same_unique_name_succeeds(
            self, mock_popen, app, custom_functions_dir, tmp_install_dir,
            mock_mycodo_user):
        """Uploaded file with a different filename but the same function_name_unique in its dict
        should succeed — the comparison is purely dict-based, not filename-based."""
        from mycodo.mycodo_flask.utils.utils_settings import settings_function_update

        # Existing module on disk: my_custom_function.py, unique name 'MY_CUSTOM_FUNCTION'
        write_existing_module(custom_functions_dir)

        # Uploaded file has a DIFFERENT filename but the SAME function_name_unique in its dict
        form_del = make_del_form(VALID_FUNCTION_UNIQUE_NAME)
        form = make_mod_form(MockFileStorage('renamed_upload.py', VALID_FUNCTION_CONTENT))

        with patch('mycodo.mycodo_flask.utils.utils_settings.INSTALL_DIRECTORY', tmp_install_dir), \
                patch('mycodo.mycodo_flask.utils.utils_settings.PATH_FUNCTIONS_CUSTOM', custom_functions_dir), \
                patch('mycodo.mycodo_flask.utils.utils_settings.CustomController') as mock_cc:
            mock_cc.query.filter.return_value.count.return_value = 0
            settings_function_update(form_del, form)

        # The existing module file should have been overwritten (keyed by unique name, not upload filename)
        expected_file = os.path.join(custom_functions_dir, 'my_custom_function.py')
        assert os.path.exists(expected_file)
        with open(expected_file, 'rb') as f:
            assert b'MY_CUSTOM_FUNCTION' in f.read()
        mock_popen.assert_called_once()

    @mock.patch('subprocess.Popen')
    def test_update_different_filename_different_unique_name_fails(
            self, mock_popen, app, custom_functions_dir, tmp_install_dir,
            mock_mycodo_user):
        """Uploaded file with a different filename AND a different function_name_unique in its dict
        should fail — even though the filename is different, the dict value must match."""
        from mycodo.mycodo_flask.utils.utils_settings import settings_function_update

        # Existing module on disk: my_custom_function.py, unique name 'MY_CUSTOM_FUNCTION'
        write_existing_module(custom_functions_dir)

        # Uploaded file has a different filename AND a different function_name_unique in its dict
        different_content = b"""FUNCTION_INFORMATION = {
    'function_name_unique': 'DIFFERENT_FUNCTION',
    'function_name': 'Different Function',
}
"""
        form_del = make_del_form(VALID_FUNCTION_UNIQUE_NAME)
        form = make_mod_form(MockFileStorage('renamed_upload.py', different_content))

        with patch('mycodo.mycodo_flask.utils.utils_settings.INSTALL_DIRECTORY', tmp_install_dir), \
                patch('mycodo.mycodo_flask.utils.utils_settings.PATH_FUNCTIONS_CUSTOM', custom_functions_dir):
            settings_function_update(form_del, form)

        mock_popen.assert_not_called()

    @mock.patch('subprocess.Popen')
    def test_update_invalid_python_fails(
            self, mock_popen, app, custom_functions_dir, tmp_install_dir,
            mock_mycodo_user):
        """An uploaded file with invalid Python should fail without touching the module."""
        from mycodo.mycodo_flask.utils.utils_settings import settings_function_update

        original_content = VALID_FUNCTION_CONTENT + b'# original\n'
        write_existing_module(custom_functions_dir, original_content)

        form_del = make_del_form(VALID_FUNCTION_UNIQUE_NAME)
        form = make_mod_form(MockFileStorage('my_custom_function.py', b'this is not valid python !@#$%'))

        with patch('mycodo.mycodo_flask.utils.utils_settings.INSTALL_DIRECTORY', tmp_install_dir), \
                patch('mycodo.mycodo_flask.utils.utils_settings.PATH_FUNCTIONS_CUSTOM', custom_functions_dir):
            settings_function_update(form_del, form)

        # Existing module should be untouched
        with open(os.path.join(custom_functions_dir, 'my_custom_function.py'), 'rb') as f:
            assert b'# original' in f.read()
        mock_popen.assert_not_called()

    @mock.patch('subprocess.Popen')
    def test_update_sideloaded_module_preserves_original_filename(
            self, mock_popen, app, custom_functions_dir, tmp_install_dir,
            mock_mycodo_user):
        """A side-loaded module (filename ≠ function_name_unique) must be updated in-place,
        preserving the original filename rather than creating a new name-derived file."""
        from mycodo.mycodo_flask.utils.utils_settings import settings_function_update

        # The side-loaded module uses an arbitrary filename unrelated to function_name_unique
        sideloaded_path = os.path.join(custom_functions_dir, 'sideloaded_custom_func.py')
        with open(sideloaded_path, 'wb') as f:
            f.write(VALID_FUNCTION_CONTENT)

        form_del = make_del_form(VALID_FUNCTION_UNIQUE_NAME)
        form = make_mod_form(MockFileStorage('sideloaded_custom_func.py', VALID_FUNCTION_CONTENT))

        # parse_function_information() returns the side-loaded file's actual path
        mock_dict = {
            VALID_FUNCTION_UNIQUE_NAME: {
                'file_path': sideloaded_path,
                'function_name': 'My Custom Function',
            }
        }

        with patch('mycodo.mycodo_flask.utils.utils_settings.INSTALL_DIRECTORY', tmp_install_dir), \
                patch('mycodo.mycodo_flask.utils.utils_settings.PATH_FUNCTIONS_CUSTOM', custom_functions_dir), \
                patch('mycodo.mycodo_flask.utils.utils_settings.parse_function_information',
                      return_value=mock_dict), \
                patch('mycodo.mycodo_flask.utils.utils_settings.CustomController') as mock_cc:
            mock_cc.query.filter.return_value.count.return_value = 0
            settings_function_update(form_del, form)

        # The side-loaded file should have been updated in-place
        assert os.path.exists(sideloaded_path)
        with open(sideloaded_path, 'rb') as f:
            assert b'MY_CUSTOM_FUNCTION' in f.read()

        # A new name-derived file must NOT have been created
        name_derived_path = os.path.join(custom_functions_dir, 'my_custom_function.py')
        assert not os.path.exists(name_derived_path)

        # Frontend reload should have been triggered
        mock_popen.assert_called_once()
        assert 'frontend_reload' in mock_popen.call_args[0][0]

    @mock.patch('subprocess.Popen')
    def test_update_sideloaded_module_overwrites_content(
            self, mock_popen, app, custom_functions_dir, tmp_install_dir,
            mock_mycodo_user):
        """Updating a side-loaded module should replace the file content at the original path."""
        from mycodo.mycodo_flask.utils.utils_settings import settings_function_update

        sideloaded_path = os.path.join(custom_functions_dir, 'sideloaded_custom_func.py')
        with open(sideloaded_path, 'wb') as f:
            f.write(VALID_FUNCTION_CONTENT + b'# old version\n')

        new_content = VALID_FUNCTION_CONTENT + b'# new version\n'
        form_del = make_del_form(VALID_FUNCTION_UNIQUE_NAME)
        form = make_mod_form(MockFileStorage('sideloaded_custom_func.py', new_content))

        mock_dict = {
            VALID_FUNCTION_UNIQUE_NAME: {
                'file_path': sideloaded_path,
                'function_name': 'My Custom Function',
            }
        }

        with patch('mycodo.mycodo_flask.utils.utils_settings.INSTALL_DIRECTORY', tmp_install_dir), \
                patch('mycodo.mycodo_flask.utils.utils_settings.PATH_FUNCTIONS_CUSTOM', custom_functions_dir), \
                patch('mycodo.mycodo_flask.utils.utils_settings.parse_function_information',
                      return_value=mock_dict), \
                patch('mycodo.mycodo_flask.utils.utils_settings.CustomController') as mock_cc:
            mock_cc.query.filter.return_value.count.return_value = 0
            settings_function_update(form_del, form)

        with open(sideloaded_path, 'rb') as f:
            content = f.read()
        assert b'# old version' not in content
        assert b'# new version' in content
