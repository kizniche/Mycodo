# coding=utf-8
""" collection of Admin endpoints """
import logging
import os
import subprocess
import flask_login
from flask import (
    Blueprint,
    redirect,
    render_template,
    flash,
    request,
    url_for
)
from flask_babel import gettext
from pkg_resources import parse_version

# Functions
from mycodo import flaskforms
from mycodo import flaskutils
from mycodo.mycodo_flask.static_routes import inject_mycodo_version
from mycodo.utils.statistics import return_stat_file_dict
from mycodo.utils.system_pi import internet
from mycodo.utils.github_release_info import github_releases

# Config
from mycodo.config import (
    BACKUP_LOG_FILE,
    BACKUP_PATH,
    INSTALL_DIRECTORY,
    MYCODO_VERSION,
    RESTORE_LOG_FILE,
    STATS_CSV,
    UPGRADE_LOG_FILE
)

logger = logging.getLogger('mycodo.mycodo_flask.admin')

blueprint = Blueprint(
    'admin_routes',
    __name__,
    static_folder='../static',
    template_folder='../templates'
)


@blueprint.context_processor
@flask_login.login_required
def inject_dictionary():
    return inject_mycodo_version()


@blueprint.route('/admin/backup', methods=('GET', 'POST'))
@flask_login.login_required
def admin_backup():
    """ Load the backup management page """
    if not flaskutils.user_has_permission('edit_settings'):
        return redirect(url_for('general_routes.home'))

    form_backup = flaskforms.Backup()

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
            backup_dirs.append(each_dir)
            full_paths.append(os.path.join(BACKUP_PATH, each_dir))

    if request.method == 'POST':
        if form_backup.backup.data:
            cmd = '{pth}/mycodo/scripts/mycodo_wrapper backup-create ' \
                  ' >> {log} 2>&1'.format(pth=INSTALL_DIRECTORY,
                                          log=BACKUP_LOG_FILE)
            subprocess.Popen(cmd, shell=True)
            flash(gettext(u"Backup in progress. It should complete within a "
                          u"few seconds to a few minutes. The backup will "
                          u"appear on this page after it completes."),
                  "success")
        elif form_backup.delete.data:
            cmd = '{pth}/mycodo/scripts/mycodo_wrapper backup-delete {dir}' \
                  ' 2>&1'.format(pth=INSTALL_DIRECTORY,
                                 dir=form_backup.selected_dir.data)
            subprocess.Popen(cmd, shell=True)
            flash(gettext(u"Deletion of backup in progress. It should "
                          u"complete within a few seconds to a few minutes. "
                          u"The backup will disappear on this page after it "
                          u"completes."),
                  "success")
        elif form_backup.restore.data:
            cmd = '{pth}/mycodo/scripts/mycodo_wrapper backup-restore ' \
                  '{backup} >> {log} 2>&1'.format(
                    pth=INSTALL_DIRECTORY,
                    backup=form_backup.full_path.data,
                    log=RESTORE_LOG_FILE)

            subprocess.Popen(cmd, shell=True)
            flash(gettext(u"Restore in progress. It should complete within a "
                          u"few seconds to a few minutes."),
                  "success")

    return render_template('admin/backup.html',
                           form_backup=form_backup,
                           backup_dirs=backup_dirs,
                           full_paths=full_paths)


@blueprint.route('/admin/statistics', methods=('GET', 'POST'))
@flask_login.login_required
def admin_statistics():
    """ Display collected statistics """
    if not flaskutils.user_has_permission('view_stats'):
        return redirect(url_for('general_routes.home'))

    try:
        statistics = return_stat_file_dict(STATS_CSV)
    except IOError:
        statistics = {}
    return render_template('admin/statistics.html',
                           statistics=statistics)


@blueprint.route('/admin/upgrade', methods=('GET', 'POST'))
@flask_login.login_required
def admin_upgrade():
    """ Display any available upgrades and option to upgrade """
    if not flaskutils.user_has_permission('edit_settings'):
        return redirect(url_for('general_routes.home'))

    if not internet():
        flash(gettext(u"Upgrade functionality is disabled because an internet "
                      u"connection was unable to be detected"),
              "error")
        return render_template('admin/upgrade.html',
                               is_internet=False)

    # Read from the upgrade status file created by the upgrade script
    # to indicate if the upgrade is running.
    try:
        with open(INSTALL_DIRECTORY + '/.upgrade') as f:
            upgrade = int(f.read(1))
    except IOError:
        try:
            with open(INSTALL_DIRECTORY + '/.upgrade', 'w') as f:
                f.write('0')
        finally:
            upgrade = 0

    if upgrade:
        if upgrade == 1:
            flash(gettext(u"An upgrade is currently in progress. Please wait "
                          u"for it to finish"),
                  "error")
        elif upgrade == 2:
            flash(gettext(u"There was an error encountered during the upgrade "
                          u"process. Check the upgrade log for details."),
                  "error")
        return render_template('admin/upgrade.html',
                               upgrade=upgrade)

    form_backup = flaskforms.Backup()
    form_upgrade = flaskforms.Upgrade()

    is_internet = True
    upgrade_available = False

    # Check for any new Mycodo releases on github
    releases = []
    try:
        maj_version = int(MYCODO_VERSION.split('.')[0])
        releases = github_releases(maj_version)
    except Exception:
        flash(gettext(u"Could not determine local mycodo version or "
                      u"online release versions"), "error")
    if len(releases):
        latest_release = releases[0]
        current_releases = []
        releases_behind = None
        for index, each_release in enumerate(releases):
            if parse_version(each_release) >= parse_version(MYCODO_VERSION):
                current_releases.append(each_release)
            if parse_version(each_release) == parse_version(MYCODO_VERSION):
                releases_behind = index
        if parse_version(releases[0]) > parse_version(MYCODO_VERSION):
            upgrade_available = True
    else:
        current_releases = []
        latest_release = '0.0.0'
        releases_behind = 0

    if request.method == 'POST':
        if form_upgrade.upgrade.data and upgrade_available:
            cmd = '{pth}/mycodo/scripts/mycodo_wrapper upgrade >> {log} ' \
                  '2>&1'.format(pth=INSTALL_DIRECTORY,
                                log=UPGRADE_LOG_FILE)
            subprocess.Popen(cmd, shell=True)
            upgrade = 1
            flash(gettext(u"The upgrade has started. The daemon will be "
                          u"stopped during the upgrade."), "success")
        else:
            flash(gettext(u"You cannot upgrade if an upgrade is not available"),
                  "error")

    return render_template('admin/upgrade.html',
                           form_backup=form_backup,
                           form_upgrade=form_upgrade,
                           current_release=MYCODO_VERSION,
                           current_releases=current_releases,
                           latest_release=latest_release,
                           releases_behind=releases_behind,
                           upgrade_available=upgrade_available,
                           upgrade=upgrade,
                           is_internet=is_internet)
