# coding=utf-8
"""collection of Admin endpoints."""
import datetime
import io
import logging
import os
import socket
import subprocess
import threading
import zipfile
from collections import OrderedDict

import flask_login
from flask import (Blueprint, flash, jsonify, make_response, redirect,
                   render_template, request, send_file, url_for)
from flask_babel import gettext
from pkg_resources import parse_version

from mycodo.config import (BACKUP_LOG_FILE, BACKUP_PATH, CAMERA_INFO,
                           DEPENDENCIES_GENERAL, DEPENDENCY_INIT_FILE,
                           DEPENDENCY_LOG_FILE, FINAL_RELEASES,
                           FORCE_UPGRADE_MASTER, FUNCTION_INFO,
                           INSTALL_DIRECTORY, METHOD_INFO, MYCODO_VERSION,
                           RESTORE_LOG_FILE, STATS_CSV, UPGRADE_INIT_FILE,
                           UPGRADE_LOG_FILE, UPGRADE_TMP_LOG_FILE)
from mycodo.databases.models import Misc
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.forms import forms_dependencies, forms_misc
from mycodo.mycodo_flask.routes_static import inject_variables
from mycodo.mycodo_flask.utils import utils_general
from mycodo.utils.actions import parse_action_information
from mycodo.utils.functions import parse_function_information
from mycodo.utils.github_release_info import MycodoRelease
from mycodo.utils.inputs import parse_input_information
from mycodo.utils.outputs import parse_output_information
from mycodo.utils.stats import return_stat_file_dict
from mycodo.utils.system_pi import (can_perform_backup, cmd_output,
                                    get_directory_size, internet)
from mycodo.utils.widgets import parse_widget_information

logger = logging.getLogger('mycodo.mycodo_flask.admin')

blueprint = Blueprint(
    'routes_admin',
    __name__,
    static_folder='../static',
    template_folder='../templates'
)


@blueprint.context_processor
@flask_login.login_required
def inject_dictionary():
    return inject_variables()


@blueprint.route('/admin/backup', methods=('GET', 'POST'))
@flask_login.login_required
def admin_backup():
    """Load the backup management page"""
    if not utils_general.user_has_permission('edit_settings'):
        return redirect(url_for('routes_general.home'))

    form_backup = forms_misc.Backup()

    backup_dirs_tmp = []
    if not os.path.isdir('/var/Mycodo-backups'):
        flash("Error: Backup directory doesn't exist.", "error")
    else:
        backup_dirs_tmp = sorted(next(os.walk(BACKUP_PATH))[1])
        backup_dirs_tmp.reverse()

    backup_dirs = []
    full_paths = []
    for each_dir in backup_dirs_tmp:
        if each_dir.startswith("Mycodo-backup-"):
            full_path = os.path.join(BACKUP_PATH, each_dir)
            backup_dirs.append((each_dir, get_directory_size(full_path) / 1000000.0))
            full_paths.append(full_path)

    if request.method == 'POST':
        if form_backup.backup.data:
            backup_size, free_before, free_after = can_perform_backup()
            if free_after / 1000000 > 50:
                cmd = "{pth}/mycodo/scripts/mycodo_wrapper backup-create" \
                      " | ts '[%Y-%m-%d %H:%M:%S]'" \
                      " >> {log} 2>&1".format(pth=INSTALL_DIRECTORY,
                                              log=BACKUP_LOG_FILE)
                subprocess.Popen(cmd, shell=True)
                flash(gettext("Backup in progress"), "success")
            else:
                flash(
                    "Not enough free space to perform a backup. A backup "
                    "requires {size_bu:.1f} MB but there is only "
                    "{size_free:.1f} MB available, which would leave "
                    "{size_after:.1f} MB after the backup. If the free space "
                    "after a backup is less than 50 MB, the backup cannot "
                    "proceed. Free up space by deleting current "
                    "backups.".format(size_bu=backup_size / 1000000,
                                      size_free=free_before / 1000000,
                                      size_after=free_after / 1000000),
                    'error')

        elif form_backup.download.data:
            def get_all_file_paths(directory):
                file_paths = []
                for root, directories, files in os.walk(directory):
                    for filename in files:
                        # join the two strings in order to form the full filepath
                        filepath = os.path.join(root, filename)
                        file_paths.append(filepath)
                return file_paths

            try:
                backup_date_version = form_backup.selected_dir.data
                download_dir = os.path.join(BACKUP_PATH, 'Mycodo-backup-{}'.format(backup_date_version))
                save_file = "Mycodo_Backup_{dv}_{host}_.zip".format(
                    dv=backup_date_version, host=socket.gethostname().replace(' ', ''))
                file_paths = get_all_file_paths(download_dir)
                string_remove = "{}".format(os.path.join(BACKUP_PATH, download_dir))

                if not os.path.isdir(download_dir):
                    flash("Directory not found: {}".format(download_dir), "error")
                else:
                    # Zip all files in the_backup directory
                    data = io.BytesIO()
                    with zipfile.ZipFile(data, 'w') as zipf:
                        # writing each file one by one
                        for file in file_paths:
                            # Remove first two directory names from zip file, so the Mycodo root is the zip root
                            zipf.write(file, file.replace(string_remove, ""))
                    data.seek(0)

                    # Send zip file to user
                    return send_file(
                        data,
                        mimetype='application/zip',
                        as_attachment=True,
                        download_name=save_file
                    )
            except Exception as err:
                flash("Error: {}".format(err), "error")

        elif form_backup.delete.data:
            cmd = "{pth}/mycodo/scripts/mycodo_wrapper backup-delete {dir}" \
                  " 2>&1".format(pth=INSTALL_DIRECTORY,
                                 dir=form_backup.selected_dir.data)
            subprocess.Popen(cmd, shell=True)
            flash(gettext("Deletion of backup in progress"),
                  "success")

        elif form_backup.restore.data:
            if not os.path.isdir(form_backup.full_path.data):
                flash("Directory not found: {}".format(form_backup.full_path.data), "error")
            else:
                cmd = "{pth}/mycodo/scripts/mycodo_wrapper backup-restore {backup}" \
                      " | ts '[%Y-%m-%d %H:%M:%S]'" \
                      " >> {log} 2>&1".format(pth=INSTALL_DIRECTORY,
                                              backup=form_backup.full_path.data,
                                              log=RESTORE_LOG_FILE)
                subprocess.Popen(cmd, shell=True)
                flash(gettext("Restore in progress"),
                      "success")

    return render_template('admin/backup.html',
                           form_backup=form_backup,
                           backup_dirs=backup_dirs,
                           full_paths=full_paths)


def install_dependencies(dependencies):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dependency_list = []
    for each_dependency in dependencies:
        if each_dependency[0] not in dependency_list:
            dependency_list.append(each_dependency[0])
    with open(DEPENDENCY_LOG_FILE, 'a+') as f:
        f.write("\n[{time}] Dependency installation beginning. Installing: {deps}\n\n".format(
            time=now, deps=", ".join(dependency_list)))

    for each_dep in dependencies:
        if each_dep[2] == 'bash-commands':
            for each_command in each_dep[1]:
                try:
                    with open(DEPENDENCY_LOG_FILE, 'a+') as f:
                        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        f.write(f"\n[{now}] Executing command: {each_command}\n")

                    command = "{cmd} | ts '[%Y-%m-%d %H:%M:%S]' >> {log} 2>&1".format(
                        cmd=each_command,
                        log=DEPENDENCY_LOG_FILE)
                    cmd_out, cmd_err, cmd_status = cmd_output(
                        command, user='root', timeout=600, cwd="/tmp")

                    with open(DEPENDENCY_LOG_FILE, 'a+') as f:
                        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        f.write(f"\n[{now}] Command returned: out: {cmd_out}, error: {cmd_err}, status: {cmd_status}\n")
                except:
                    logger.exception("Executing command")
        else:
            cmd = "{pth}/mycodo/scripts/mycodo_wrapper install_dependency {dep}" \
                  " | ts '[%Y-%m-%d %H:%M:%S]' >> {log} 2>&1".format(
                    pth=INSTALL_DIRECTORY,
                    log=DEPENDENCY_LOG_FILE,
                    dep=each_dep[1])
            dep = subprocess.Popen(cmd, shell=True)
            dep.wait()
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(DEPENDENCY_LOG_FILE, 'a+') as f:
                f.write("\n[{time}] End install of {dep}\n\n".format(
                    time=now, dep=each_dep[0]))

    cmd = "{pth}/mycodo/scripts/mycodo_wrapper update_permissions" \
          " | ts '[%Y-%m-%d %H:%M:%S]' >> {log}  2>&1".format(
            pth=INSTALL_DIRECTORY,
            log=DEPENDENCY_LOG_FILE)
    init = subprocess.Popen(cmd, shell=True)
    init.wait()

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(DEPENDENCY_LOG_FILE, 'a+') as f:
        f.write("\n[{time}] #### Dependencies installed. Restarting frontend and backend...".format(time=now))

    with open(DEPENDENCY_INIT_FILE, 'w') as f:
        f.write('0')

    cmd = "{pth}/mycodo/scripts/mycodo_wrapper daemon_restart" \
          " | ts '[%Y-%m-%d %H:%M:%S]' >> {log}  2>&1".format(
            pth=INSTALL_DIRECTORY,
            log=DEPENDENCY_LOG_FILE)
    init = subprocess.Popen(cmd, shell=True)
    init.wait()

    cmd = "{pth}/mycodo/scripts/mycodo_wrapper frontend_reload" \
          " | ts '[%Y-%m-%d %H:%M:%S]' >> {log}  2>&1".format(
            pth=INSTALL_DIRECTORY,
            log=DEPENDENCY_LOG_FILE)
    init = subprocess.Popen(cmd, shell=True)
    init.wait()

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(DEPENDENCY_LOG_FILE, 'a+') as f:
        f.write("\n\n[{time}] #### Dependency install complete.\n\n".format(time=now))


@blueprint.route('/admin/dependency_install/<device>', methods=('GET', 'POST'))
@flask_login.login_required
def admin_dependency_install(device):
    """Install Dependencies."""
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }

    try:
        device_unmet_dependencies, _, _ = utils_general.return_dependencies(device)
        with open(DEPENDENCY_INIT_FILE, 'w') as f:
            f.write('1')
        install_deps = threading.Thread(
            target=install_dependencies,
            args=(device_unmet_dependencies,))
        install_deps.start()
        messages["success"].append("Dependency install initiated")
    except Exception as err:
        messages["error"].append("Error: {}".format(err))

    return jsonify(data={
        'messages': messages
    })


@blueprint.route('/admin/dependencies', methods=('GET', 'POST'))
@flask_login.login_required
def admin_dependencies_main():
    return redirect(url_for('routes_admin.admin_dependencies', device='0'))


@blueprint.route('/admin/dependencies/<device>', methods=('GET', 'POST'))
@flask_login.login_required
def admin_dependencies(device):
    """Display Dependency page"""
    form_dependencies = forms_dependencies.Dependencies()

    if device != '0':
        # Only loading a single dependency page
        device_unmet_dependencies, _, _ = utils_general.return_dependencies(device)
    elif form_dependencies.device.data:
        device_unmet_dependencies, _, _ = utils_general.return_dependencies(form_dependencies.device.data)
    else:
        device_unmet_dependencies = []

    unmet_dependencies = OrderedDict()
    unmet_exist = False
    met_dependencies = []
    met_exist = False
    unmet_list = {}
    install_in_progress = False
    device_name = None
    dependencies_message = ""

    # Read from the dependency status file created by the upgrade script
    # to indicate if the upgrade is running.
    try:
        with open(DEPENDENCY_INIT_FILE) as f:
            dep = int(f.read(1))
    except (IOError, ValueError):
        try:
            with open(DEPENDENCY_INIT_FILE, 'w') as f:
                f.write('0')
        finally:
            dep = 0

    if dep:
        install_in_progress = True

    list_dependencies = [
        parse_function_information(),
        parse_action_information(),
        parse_input_information(),
        parse_output_information(),
        parse_widget_information(),
        CAMERA_INFO,
        FUNCTION_INFO,
        METHOD_INFO,
        DEPENDENCIES_GENERAL
    ]
    for each_section in list_dependencies:
        for each_device in each_section:

            if device in each_section:
                # Determine if a message for the dependencies exists
                if "dependencies_message" in each_section[device]:
                    dependencies_message = each_section[device]["dependencies_message"]

                # Find friendly name for device
                for each_device_, each_val in each_section[device].items():
                    if each_device_ in ['name',
                                        'input_name',
                                        'output_name',
                                        'function_name',
                                        'widget_name']:
                        device_name = each_val
                        break

            # Only get all dependencies when not loading a single dependency page
            if device == '0':
                # Determine if there are any unmet dependencies for every device
                dep_unmet, dep_met, _ = utils_general.return_dependencies(each_device)

                unmet_dependencies.update({
                    each_device: dep_unmet
                })
                if dep_unmet:
                    unmet_exist = True

                # Determine if there are any met dependencies
                if dep_met:
                    if each_device not in met_dependencies:
                        met_dependencies.append(each_device)
                        met_exist = True

                # Find all the devices that use each unmet dependency
                if unmet_dependencies[each_device]:
                    for each_dep in unmet_dependencies[each_device]:
                        # Determine if the second element of a 4-element tuple is a list, convert it to a tuple
                        if (type(each_dep) == tuple and
                                len(each_dep) == 4 and
                                type(each_dep[1]) == list):
                            each_dep = list(each_dep)
                            each_dep[1] = tuple(each_dep[1])
                            each_dep = tuple(each_dep)

                        # Determine if the third element of a 3-element tuple is a list, convert it to a tuple
                        if (type(each_dep) == tuple and
                                len(each_dep) == 3 and
                                type(each_dep[2]) == list):
                            each_dep = list(each_dep)
                            each_dep[2] = tuple(each_dep[2])
                            each_dep = tuple(each_dep)

                        if each_dep not in unmet_list:
                            unmet_list[each_dep] = []
                        if each_device not in unmet_list[each_dep]:
                            unmet_list[each_dep].append(each_device)

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_controllers'):
            return redirect(url_for('routes_admin.admin_dependencies', device=device))

        if form_dependencies.install.data:
            with open(DEPENDENCY_INIT_FILE, 'w') as f:
                f.write('1')
            install_deps = threading.Thread(
                target=install_dependencies,
                args=(device_unmet_dependencies,))
            install_deps.start()

        return redirect(url_for('routes_admin.admin_dependencies', device=device))

    return render_template('admin/dependencies.html',
                           measurements=parse_input_information(),
                           unmet_list=unmet_list,
                           dependencies_message=dependencies_message,
                           device=device,
                           device_name=device_name,
                           install_in_progress=install_in_progress,
                           unmet_dependencies=unmet_dependencies,
                           unmet_exist=unmet_exist,
                           met_dependencies=met_dependencies,
                           met_exist=met_exist,
                           form_dependencies=form_dependencies,
                           device_unmet_dependencies=device_unmet_dependencies)


@blueprint.route('/admin/dependency_status', methods=('GET', 'POST'))
@flask_login.login_required
def admin_dependency_status():
    """Return the last 30 lines of the dependency log."""
    if os.path.isfile(DEPENDENCY_LOG_FILE):
        command = 'tail -n 40 {log}'.format(log=DEPENDENCY_LOG_FILE)
        log = subprocess.Popen(
            command, stdout=subprocess.PIPE, shell=True)
        (log_output, _) = log.communicate()
        log.wait()
        log_output = log_output.decode("utf-8")
    else:
        log_output = 'Dependency log not found. If a dependency install was ' \
                     'just initialized, please wait...'
    response = make_response(log_output)
    response.headers["content-type"] = "text/plain"
    return response


@blueprint.route('/admin/statistics', methods=('GET', 'POST'))
@flask_login.login_required
def admin_statistics():
    """Display collected statistics."""
    if not utils_general.user_has_permission('view_stats'):
        return redirect(url_for('routes_general.home'))

    try:
        statistics = return_stat_file_dict(STATS_CSV)
    except IOError:
        statistics = {}
    return render_template('admin/statistics.html',
                           statistics=statistics)


@blueprint.route('/admin/upgrade_status', methods=('GET', 'POST'))
@flask_login.login_required
def admin_upgrade_status():
    """Return the last 30 lines of the upgrade log."""
    if os.path.isfile(UPGRADE_TMP_LOG_FILE):
        command = 'cat {log}'.format(log=UPGRADE_TMP_LOG_FILE)
        log = subprocess.Popen(
            command, stdout=subprocess.PIPE, shell=True)
        (log_output, _) = log.communicate()
        log.wait()
        log_output = log_output.decode("utf-8")
    else:
        log_output = 'Upgrade log not found. If an upgrade was just ' \
                     'initialized, please wait...'
    response = make_response(log_output)
    response.headers["content-type"] = "text/plain"
    return response


@blueprint.route('/admin/upgrade', methods=('GET', 'POST'))
@flask_login.login_required
def admin_upgrade():
    """Display any available upgrades and option to upgrade"""
    if not utils_general.user_has_permission('edit_settings'):
        return redirect(url_for('routes_general.home'))

    misc = Misc.query.first()
    if not internet(host=misc.net_test_ip,
                    port=misc.net_test_port,
                    timeout=misc.net_test_timeout):
        return render_template('admin/upgrade.html',
                               is_internet=False)

    is_internet = True

    # Read from the upgrade status file created by the upgrade script
    # to indicate if the upgrade is running.
    try:
        with open(UPGRADE_INIT_FILE) as f:
            upgrade = int(f.read(1))
    except Exception:
        try:
            with open(UPGRADE_INIT_FILE, 'w') as f:
                f.write('0')
        finally:
            upgrade = 0

    if upgrade:
        if upgrade == 2:
            flash(gettext("There was an error encountered during the upgrade"
                          " process. Check the upgrade log for details."),
                  "error")
        return render_template('admin/upgrade.html',
                               current_release=MYCODO_VERSION,
                               is_internet=is_internet,
                               upgrade=upgrade)

    form_backup = forms_misc.Backup()
    form_upgrade = forms_misc.Upgrade()

    upgrade_available = False

    # Check for any new Mycodo releases on github
    mycodo_releases_check = MycodoRelease()
    (upgrade_exists,
     releases,
     mycodo_releases,
     current_latest_release,
     errors) = mycodo_releases_check.github_upgrade_exists()

    if errors:
        for each_error in errors:
            flash(each_error, 'error')

    if releases and current_latest_release and "." in current_latest_release:
        current_latest_major_version = current_latest_release.split('.')[0]
        current_major_release = releases[0]
        current_releases = []
        releases_behind = None
        for index, each_release in enumerate(releases):
            if parse_version(each_release) >= parse_version(MYCODO_VERSION):
                current_releases.append(each_release)
            if parse_version(each_release) == parse_version(MYCODO_VERSION):
                releases_behind = index
        if upgrade_exists:
            upgrade_available = True
    else:
        current_releases = []
        current_latest_major_version = '0'
        current_major_release = '0.0.0'
        releases_behind = 0

    # Update database to reflect the current upgrade status
    mod_misc = Misc.query.first()
    if mod_misc.mycodo_upgrade_available != upgrade_available:
        mod_misc.mycodo_upgrade_available = upgrade_available
        db.session.commit()

    def not_enough_space_upgrade():
        backup_size, free_before, free_after = can_perform_backup()
        if free_after / 1000000 < 50:
            flash(
                "A backup must be performed during an upgrade and there is "
                "not enough free space to perform a backup. A backup "
                "requires {size_bu:.1f} MB but there is only {size_free:.1f} "
                "MB available, which would leave {size_after:.1f} MB after "
                "the backup. If the free space after a backup is less than 50"
                " MB, the backup cannot proceed. Free up space by deleting "
                "current backups.".format(size_bu=backup_size / 1000000,
                                          size_free=free_before / 1000000,
                                          size_after=free_after / 1000000),
                'error')
            return True
        else:
            return False

    if request.method == 'POST':
        if (form_upgrade.upgrade.data and
                (upgrade_available or FORCE_UPGRADE_MASTER)):
            if not_enough_space_upgrade():
                pass
            elif FORCE_UPGRADE_MASTER:
                try:
                    os.remove(UPGRADE_TMP_LOG_FILE)
                except FileNotFoundError:
                    pass
                cmd = "{pth}/mycodo/scripts/mycodo_wrapper upgrade-master" \
                      " | ts '[%Y-%m-%d %H:%M:%S]' 2>&1 | tee -a {log} {tmp_log}".format(
                    pth=INSTALL_DIRECTORY,
                    log=UPGRADE_LOG_FILE,
                    tmp_log=UPGRADE_TMP_LOG_FILE)
                subprocess.Popen(cmd, shell=True)

                upgrade = 1
                flash(gettext("The upgrade (from master branch) has started"), "success")
            else:
                try:
                    os.remove(UPGRADE_TMP_LOG_FILE)
                except FileNotFoundError:
                    pass
                cmd = "{pth}/mycodo/scripts/mycodo_wrapper upgrade-release-major {current_maj_version}" \
                      " | ts '[%Y-%m-%d %H:%M:%S]' 2>&1 | tee -a {log} {tmp_log}".format(
                    current_maj_version=MYCODO_VERSION.split('.')[0],
                    pth=INSTALL_DIRECTORY,
                    log=UPGRADE_LOG_FILE,
                    tmp_log=UPGRADE_TMP_LOG_FILE)
                subprocess.Popen(cmd, shell=True)

                upgrade = 1
                mod_misc = Misc.query.first()
                mod_misc.mycodo_upgrade_available = False
                db.session.commit()
                flash(gettext("The upgrade has started"), "success")
        elif (form_upgrade.upgrade_next_major_version.data and
                upgrade_available):
            if not not_enough_space_upgrade():
                try:
                    os.remove(UPGRADE_TMP_LOG_FILE)
                except FileNotFoundError:
                    pass
                cmd = "{pth}/mycodo/scripts/mycodo_wrapper upgrade-release-wipe {ver}" \
                      " | ts '[%Y-%m-%d %H:%M:%S]' 2>&1 | tee -a {log} {tmp_log}".format(
                    pth=INSTALL_DIRECTORY,
                    ver=current_latest_major_version,
                    log=UPGRADE_LOG_FILE,
                    tmp_log=UPGRADE_TMP_LOG_FILE)
                subprocess.Popen(cmd, shell=True)

                upgrade = 1
                mod_misc = Misc.query.first()
                mod_misc.mycodo_upgrade_available = False
                db.session.commit()
                flash(gettext(
                    "The major version upgrade has started"), "success")
        else:
            flash(gettext(
                "You cannot upgrade if an upgrade is not available"),
                "error")

    return render_template('admin/upgrade.html',
                           final_releases=FINAL_RELEASES,
                           force_upgrade_master=FORCE_UPGRADE_MASTER,
                           form_backup=form_backup,
                           form_upgrade=form_upgrade,
                           current_release=MYCODO_VERSION,
                           current_releases=current_releases,
                           current_major_release=current_major_release,
                           current_latest_release=current_latest_release,
                           current_latest_major_version=current_latest_major_version,
                           releases_behind=releases_behind,
                           upgrade_available=upgrade_available,
                           upgrade=upgrade,
                           is_internet=is_internet)
