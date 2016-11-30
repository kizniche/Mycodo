# coding=utf-8
""" collection of Admin endpoints """
import logging
import os
import subprocess

from flask import (Blueprint,
                   redirect,
                   render_template,
                   flash,
                   request,
                   session,
                   url_for)
from pkg_resources import parse_version

from utils.statistics import return_stat_file_dict
from utils.system_pi import cmd_output
from utils.system_pi import internet
from utils.github_release_info import github_releases

from mycodo import flaskforms
from mycodo.mycodo_flask.general_routes import (before_blueprint_request,
                                                inject_mycodo_version,
                                                logged_in)

from config import INSTALL_DIRECTORY
from config import MYCODO_VERSION
from config import STATS_CSV

logger = logging.getLogger('mycodo.mycodo_flask.admin')

blueprint = Blueprint('admin_routes', __name__, static_folder='../static', template_folder='../templates')
blueprint.before_request(before_blueprint_request)  # check if admin was created


@blueprint.context_processor
def inject_dictionary():
    return inject_mycodo_version()


@blueprint.route('/admin/backup', methods=('GET', 'POST'))
def admin_backup():
    """ Load the backup management page """
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    if session['user_group'] == 'guest':
        flash("Guests are not permitted to view backups.", "error")
        return redirect('/')

    formBackup = flaskforms.Backup()

    backup_dirs = []
    if not os.path.isdir('/var/Mycodo-backups'):
        flash("Error: Backup directory doesn't exist.", "error")
    else:
        backup_dirs = sorted(next(os.walk('/var/Mycodo-backups'))[1])

    if request.method == 'POST':
        form_name = request.form['form-name']
        if form_name == 'restore':
            if formBackup.restore.data:
                flash("Restore functionality is not currently enabled.",
                      "error")
                # formUpdate.restore.data
                # restore_command = INSTALL_DIRECTORY+'/mycodo/scripts/mycodo_wrapper restore '+ +'  >> /var/log/mycodo/mycodorestore.log 2>&1'
                # subprocess.Popen(restore_command, shell=True)

    return render_template('admin/backup.html',
                           formBackup=formBackup,
                           backups_sorted=backup_dirs)


@blueprint.route('/admin/statistics', methods=('GET', 'POST'))
def admin_statistics():
    """ Display collected statistics """
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    if session['user_group'] == 'guest':
        flash("Guests are not permitted to view statistics.", "error")
        return redirect('/')

    try:
        statistics = return_stat_file_dict(STATS_CSV)
    except IOError:
        statistics = {}
    return render_template('admin/statistics.html',
                           statistics=statistics)


@blueprint.route('/admin/upgrade', methods=('GET', 'POST'))
def admin_upgrade():
    """ Display any available upgrades and option to upgrade """
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    if session['user_group'] == 'guest':
        flash("Guests are not permitted to view the upgrade panel.",
              "error")
        return redirect('/')

    if not internet():
        flash("Upgrade functionality is disabled because an internet "
              "connection was unable to be detected.", "error")
        return render_template('admin/upgrade.html',
                               is_internet=False)

    # Read from the update status file created by the upgrade script
    # to indicate if the update is running.
    try:
        with open(INSTALL_DIRECTORY + '/.updating') as f:
            updating = int(f.read(1))
    except IOError:
        try:
            with open(INSTALL_DIRECTORY + '/.updating', 'w') as f:
                f.write('0')
        finally:
            updating = 0

    if updating:
        flash("An upgrade is currently in progress. "
              "Please wait for it to finish.", "error")
        return render_template('admin/upgrade.html',
                               updating=True)

    formBackup = flaskforms.Backup()
    formUpdate = flaskforms.Update()

    is_internet = True
    updating = 0
    update_available = False

    # Check for any new Mycodo releases on github
    releases = github_releases('kizniche', 'Mycodo', 4)
    latest_release = releases[0]
    current_releases = []
    releases_behind = None
    for index, each_release in enumerate(releases):
        if parse_version(each_release) >= parse_version(MYCODO_VERSION):
            current_releases.append(each_release)
        if parse_version(each_release) == parse_version(MYCODO_VERSION):
            releases_behind = index
    if parse_version(releases[0]) > parse_version(MYCODO_VERSION):
        update_available = True

    # Check for new commits of this repository on github
    # cmd_output("git fetch origin", su_mycodo=False)
    # current_commit, _, _ = cmd_output("git rev-parse --short HEAD", su_mycodo=False)
    # commits_behind, _, _ = cmd_output("git log --oneline | head -n 1", su_mycodo=False)
    # commits_behind_list = commits_behind.split('\n')
    # commits_ahead, commits_ahead_err, _ = cmd_output("git log --oneline master...origin/master", su_mycodo=False)
    # commits_ahead_list = commits_ahead.split('\n')
    # if commits_ahead and commits_ahead_err is None:
    #     update_available = True

    if request.method == 'POST':
        if formUpdate.update.data and update_available:
            subprocess.Popen(
                INSTALL_DIRECTORY + '/mycodo/scripts/mycodo_wrapper upgrade >> /var/log/mycodo/mycodoupdate.log 2>&1',
                shell=True)
            updating = 1
            flash("The upgrade has started. The daemon will be "
                  "stopped during the upgrade. Give the "
                  "process several minutes to complete "
                  "before doing anything. It may seem "
                  "unresponsive at times. When the update "
                  "has successfully finished, the daemon "
                  "status indicator at the top left will "
                  "turn from red to green. You can monitor "
                  "the update progress under Tools->Mycodo Logs"
                  "->Update Log.", "success")
        else:
            flash("You cannot update if an update is not available",
                  "error")

    return render_template('admin/upgrade.html',
                           formBackup=formBackup,
                           formUpdate=formUpdate,
                           # current_commit=current_commit,
                           # commits_ahead=commits_ahead_list,
                           # commits_behind=commits_behind_list,
                           current_release=MYCODO_VERSION,
                           current_releases=current_releases,
                           latest_release=latest_release,
                           releases_behind=releases_behind,
                           update_available=update_available,
                           updating=updating,
                           is_internet=is_internet)
