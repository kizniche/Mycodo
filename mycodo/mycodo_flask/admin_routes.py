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
from mycodo.mycodo_flask.general_routes import inject_mycodo_version
from utils.statistics import return_stat_file_dict
from utils.system_pi import internet
from utils.github_release_info import github_releases

# Config
from config import (
    INSTALL_DIRECTORY,
    MYCODO_VERSION,
    STATS_CSV
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

    backup_dirs = []
    if not os.path.isdir('/var/Mycodo-backups'):
        flash("Error: Backup directory doesn't exist.", "error")
    else:
        backup_dirs = sorted(next(os.walk('/var/Mycodo-backups'))[1])
        backup_dirs.reverse()

    backup_dirs_filtered = []
    for each_dir in backup_dirs:
        if each_dir.startswith("Mycodo-backup-"):
            backup_dirs_filtered.append(each_dir)

    if request.method == 'POST':
        form_name = request.form['form-name']
        if form_name == 'restore':
            if form_backup.restore.data:
                flash("Restore functionality is not currently enabled.",
                      "error")
                # formUpdate.restore.data
                # restore_command = '{path}/mycodo/scripts/mycodo_wrapper ' \
                #                   'restore >> /var/log/mycodo/mycodorestore.log 2>&1'.format(
                #                     path=INSTALL_DIRECTORY)
                # subprocess.Popen(restore_command, shell=True)

    return render_template('admin/backup.html',
                           form_backup=form_backup,
                           backup_dirs=backup_dirs_filtered)


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
        flash(gettext("Upgrade functionality is disabled because an internet "
                      "connection was unable to be detected"), "error")
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
            flash(gettext("An upgrade is currently in progress. Please wait "
                          "for it to finish"), "error")
        elif upgrade == 2:
            flash(gettext("There was an error encountered during the upgrade "
                          "process. Check the upgrade log for details."),
                  "error")
        return render_template('admin/upgrade.html',
                               upgrade=upgrade)

    form_backup = flaskforms.Backup()
    form_upgrade = flaskforms.Upgrade()

    is_internet = True
    upgrade_available = False

    # Check for any new Mycodo releases on github
    releases = github_releases(4)
    if len(releases) > 0:
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
            subprocess.Popen('{path}/mycodo/scripts/mycodo_wrapper upgrade >>'
                             ' /var/log/mycodo/mycodoupgrade.log 2>&1'.format(
                                path=INSTALL_DIRECTORY),
                             shell=True)
            upgrade = 1
            flash(gettext("The upgrade has started. The daemon will be "
                          "stopped during the upgrade."), "success")
        else:
            flash(gettext("You cannot upgrade if an upgrade is not available"),
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
