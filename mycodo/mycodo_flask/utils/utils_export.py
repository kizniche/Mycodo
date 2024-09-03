# -*- coding: utf-8 -*-
import datetime
import logging
import os
import shutil
import socket
import subprocess
import threading
import time
import zipfile

from flask import send_file, url_for
from packaging.version import parse
from werkzeug.utils import secure_filename

from mycodo.config import (ALEMBIC_VERSION, DATABASE_NAME, DOCKER_CONTAINER, IMPORT_LOG_FILE,
                           INSTALL_DIRECTORY, MYCODO_VERSION,
                           PATH_ACTIONS_CUSTOM, PATH_FUNCTIONS_CUSTOM,
                           PATH_TEMPLATE_USER, PATH_INPUTS_CUSTOM,
                           PATH_OUTPUTS_CUSTOM, PATH_PYTHON_CODE_USER,
                           PATH_USER_SCRIPTS, PATH_WIDGETS_CUSTOM,
                           SQL_DATABASE_MYCODO, DATABASE_PATH)
from mycodo.config_translations import TRANSLATIONS
from mycodo.mycodo_flask.utils.utils_general import (flash_form_errors,
                                                     flash_success_errors)
from mycodo.scripts.measurement_db import get_influxdb_info
from mycodo.utils.system_pi import assure_path_exists, cmd_output
from mycodo.utils.tools import (create_measurements_export,
                                create_settings_export)
from mycodo.utils.utils import append_to_log
from mycodo.utils.widget_generate_html import generate_widget_html

logger = logging.getLogger(__name__)

#
# Export
#

def export_measurements(form):
    """
    Take user input to query the InfluxDB and return a CSV file of timestamps
    and measurement values
    """
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['export']['title'],
        controller=TRANSLATIONS['measurement']['title'])
    error = []

    if form.validate():
        try:
            if not error:
                start_time = form.date_range.data.split(' - ')[0]
                start_seconds = int(time.mktime(
                    time.strptime(start_time, '%m/%d/%Y %H:%M')))
                end_time = form.date_range.data.split(' - ')[1]
                end_seconds = int(time.mktime(
                    time.strptime(end_time, '%m/%d/%Y %H:%M')))

                unique_id = form.measurement.data.split(',')[0]
                measurement_id = form.measurement.data.split(',')[1]

                url = '/export_data/{id}/{meas}/{start}/{end}'.format(
                    id=unique_id,
                    meas=measurement_id,
                    start=start_seconds, end=end_seconds)
                return url
        except Exception as err:
            error.append(f"Error: {err}")
    else:
        flash_form_errors(form)
        return

    flash_success_errors(error, action, url_for('routes_page.page_export'))


def export_settings():
    """
    Save the Mycodo settings database (mycodo.db) to a zip file and serve it
    to the user
    """
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['export']['title'],
        controller=TRANSLATIONS['settings']['title'])
    error = []

    try:
        status, data = create_settings_export()
        if not status:
            return send_file(
                data,
                mimetype='application/zip',
                as_attachment=True,
                download_name=
                    'Mycodo_{mver}_Settings_{aver}_{host}_{dt}.zip'.format(
                        mver=MYCODO_VERSION, aver=ALEMBIC_VERSION,
                        host=socket.gethostname().replace(' ', ''),
                        dt=datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
            )
        else:
            error.append(data)
    except Exception as err:
        error.append(f"Error: {err}")

    flash_success_errors(error, action, url_for('routes_page.page_export'))


def export_influxdb():
    """
    Save the Mycodo InfluxDB database in the Enterprise-compatible format, zip
    archive it, and serve it to the user.
    """
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['export']['title'],
        controller=TRANSLATIONS['measurement']['title'])
    error = []

    try:
        influxdb_info = get_influxdb_info()
        if influxdb_info['influxdb_host'] and influxdb_info['influxdb_version']:
            status, data = create_measurements_export(influxdb_info['influxdb_version'])
            if not status:
                return send_file(
                    data,
                    mimetype='application/zip',
                    as_attachment=True,
                    download_name=
                    'Mycodo_{mv}_Influxdb_{iv}_{host}_{dt}.zip'.format(
                        mv=MYCODO_VERSION, iv=influxdb_info['influxdb_version'],
                        host=socket.gethostname().replace(' ', ''),
                        dt=datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")))
            else:
                error.append(data)
        else:
            error.append("Could not determine Influxdb host/version")
    except Exception as err:
        error.append(f"Error: {err}")

    flash_success_errors(error, action, url_for('routes_page.page_export'))


#
# Import
#

def thread_import_settings(tmp_folder):
    logger.info("Finishing up settings import with thread_import_settings()")

    try:
        # Initialize
        cmd = f"{INSTALL_DIRECTORY}/mycodo/scripts/mycodo_wrapper initialize | ts '[%Y-%m-%d %H:%M:%S]' >> {IMPORT_LOG_FILE} 2>&1"
        _, _, _ = cmd_output(cmd, user="root")

        # Upgrade database
        append_to_log(IMPORT_LOG_FILE, f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Upgrading database\n")
        cmd = f"{INSTALL_DIRECTORY}/mycodo/scripts/mycodo_wrapper upgrade_database | ts '[%Y-%m-%d %H:%M:%S]' >> {IMPORT_LOG_FILE} 2>&1"
        _, _, _ = cmd_output(cmd, user="root")

        # Install/update dependencies (could take a while)
        append_to_log(IMPORT_LOG_FILE, f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Installing dependencies (this can take a while)...\n")
        cmd = f"{INSTALL_DIRECTORY}/mycodo/scripts/mycodo_wrapper update_dependencies | ts '[%Y-%m-%d %H:%M:%S]' >> {IMPORT_LOG_FILE} 2>&1"
        _, _, _ = cmd_output(cmd, user="root")

        # Generate widget HTML
        generate_widget_html()

        # Initialize
        cmd = f"{INSTALL_DIRECTORY}/mycodo/scripts/mycodo_wrapper initialize | ts '[%Y-%m-%d %H:%M:%S]' >> {IMPORT_LOG_FILE} 2>&1"
        _, _, _ = cmd_output(cmd, user="root")

        # Start Mycodo daemon (backend)
        append_to_log(IMPORT_LOG_FILE, f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Restarting backend")
        if DOCKER_CONTAINER:
            subprocess.Popen('docker start mycodo_daemon 2>&1', shell=True)
        else:
            cmd = f"{INSTALL_DIRECTORY}/mycodo/scripts/mycodo_wrapper daemon_restart | ts '[%Y-%m-%d %H:%M:%S]' >> {IMPORT_LOG_FILE} 2>&1"
            a, b, c = cmd_output(cmd, user="root")

        # Delete tmp directory if it exists
        if os.path.isdir(tmp_folder):
            shutil.rmtree(tmp_folder)

        # Reload Mycodo Flask (frontend)
        append_to_log(IMPORT_LOG_FILE, f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Reloading frontend")
        if DOCKER_CONTAINER:
            subprocess.Popen('docker start mycodo_flask 2>&1', shell=True)
        else:
            cmd = f"{INSTALL_DIRECTORY}/mycodo/scripts/mycodo_wrapper frontend_reload | ts '[%Y-%m-%d %H:%M:%S]' >> {IMPORT_LOG_FILE} 2>&1"
            _, _, _ = cmd_output(cmd, user="root")
    except:
        logger.exception("thread_import_settings()")

    append_to_log(IMPORT_LOG_FILE, f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Settings Import complete")
    logger.info("Settings import complete")


def import_settings(form):
    """
    Receive a zip file containing a Mycodo settings database that was
    exported with export_settings(), then back up the current Mycodo settings
    database and implement the one form the zip in its place.
    """
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['import']['title'],
        controller=TRANSLATIONS['settings']['title'])
    error = []

    try:
        logger.info("Beginning Settings Import")
        append_to_log(IMPORT_LOG_FILE, f"\n\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Settings Import initiated")
        correct_format = 'Mycodo_MYCODOVERSION_Settings_DBVERSION_HOST_DATETIME.zip'
        upload_folder = os.path.join(INSTALL_DIRECTORY, 'upload')
        tmp_folder = os.path.join(upload_folder, 'mycodo_db_tmp')
        full_path = None

        if not form.settings_import_file.data:
            error.append('No file present')
        elif form.settings_import_file.data.filename == '':
            error.append('No file name')
        else:
            # Split the uploaded file into parts
            file_name = form.settings_import_file.data.filename
            name = file_name.rsplit('.', 1)[0]
            extension = file_name.rsplit('.', 1)[1].lower()
            name_split = name.split('_')

            # Split the correctly-formatted filename into parts
            correct_name = correct_format.rsplit('.', 1)[0]
            correct_name_1 = correct_name.split('_')[0]
            correct_name_2 = correct_name.split('_')[2]
            correct_extension = correct_format.rsplit('.', 1)[1].lower()

            # Compare the uploaded filename parts to the correct parts
            try:
                if name_split[0] != correct_name_1:
                    error.append(f"Invalid file name: {file_name}: {name_split[0]} != {correct_name_1}.")
                    error.append(f"Correct format is: {correct_format}")
                elif name_split[2] != correct_name_2:
                    error.append(f"Invalid file name: {file_name}: {name_split[2]} != {correct_name_2}")
                    error.append(f"Correct format is: {correct_format}")
                elif extension != correct_extension:
                    error.append("Extension not 'zip'")
                elif parse(name_split[1]) > parse(MYCODO_VERSION):
                    error.append(
                        f"Invalid Mycodo version: {name_split[1]} > {MYCODO_VERSION}. "
                        f"Only databases <= {name_split[1]} can be imported")
            except Exception as err:
                error.append(f"Exception while verifying file name: {err}")

        if not error:
            logger.info("Saving import file")
            append_to_log(IMPORT_LOG_FILE, f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Saving import file")
            # Save file to upload directory
            filename = secure_filename(
                form.settings_import_file.data.filename)
            full_path = os.path.join(tmp_folder, filename)
            assure_path_exists(upload_folder)
            assure_path_exists(tmp_folder)
            append_to_log(IMPORT_LOG_FILE, f"\n\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Saving {filename} to {tmp_folder}")
            form.settings_import_file.data.save(
                os.path.join(tmp_folder, filename))

            # Check if contents of zip file are correct
            try:
                file_list = zipfile.ZipFile(full_path, 'r').namelist()
                if DATABASE_NAME not in file_list:
                    error.append(f"{DATABASE_NAME} not found in zip: {', '.join(file_list)}")
            except Exception as err:
                error.append(f"Exception checking files in zip: {err}")

        if not error:
            logger.info("Unzipping import file")
            append_to_log(IMPORT_LOG_FILE, f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Unzipping import file")
            # Unzip file
            try:
                assure_path_exists(tmp_folder)
                zip_ref = zipfile.ZipFile(full_path, 'r')
                append_to_log(IMPORT_LOG_FILE, f"\n\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Extracting {full_path} to {tmp_folder}")
                zip_ref.extractall(tmp_folder)
                zip_ref.close()
            except Exception as err:
                error.append(f"Exception while extracting zip file: {err}")

        if not error:
            logger.info("Stopping daemon and copying files")
            append_to_log(IMPORT_LOG_FILE, f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Stopping daemon and copying files")
            try:
                if DOCKER_CONTAINER:
                    subprocess.Popen('docker stop mycodo_daemon 2>&1', shell=True)
                else:
                    # Stop Mycodo daemon (backend)
                    cmd = f"{INSTALL_DIRECTORY}/mycodo/scripts/mycodo_wrapper daemon_stop"
                    _, _, _ = cmd_output(cmd, user="root")

                # Backup current database and replace with extracted mycodo.db
                imported_database = os.path.join(tmp_folder, DATABASE_NAME)
                backup_name = f"{SQL_DATABASE_MYCODO}.backup_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
                full_path_backup = os.path.join(DATABASE_PATH, backup_name)

                append_to_log(IMPORT_LOG_FILE,
                              f"\n\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Renaming {SQL_DATABASE_MYCODO} to {full_path_backup}")
                os.rename(SQL_DATABASE_MYCODO, full_path_backup)  # rename current database to backup name
                append_to_log(IMPORT_LOG_FILE,
                              f"\n\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Moving {imported_database} to {SQL_DATABASE_MYCODO}")
                shutil.move(imported_database, SQL_DATABASE_MYCODO)  # move unzipped database to Mycodo

                delete_directories = [
                    PATH_FUNCTIONS_CUSTOM,
                    PATH_ACTIONS_CUSTOM,
                    PATH_INPUTS_CUSTOM,
                    PATH_OUTPUTS_CUSTOM,
                    PATH_WIDGETS_CUSTOM,
                    PATH_USER_SCRIPTS,
                    PATH_TEMPLATE_USER,
                    PATH_PYTHON_CODE_USER
                ]

                # Delete custom functions/inputs/outputs/widgets and generated HTML/Python code
                for each_dir in delete_directories:
                    append_to_log(IMPORT_LOG_FILE, f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Deleting directory: {each_dir}")
                    if not os.path.exists(each_dir):
                        continue
                    for folder_name, sub_folders, filenames in os.walk(each_dir):
                        for filename in filenames:
                            if filename == "__init__.py":
                                continue
                            file_path = os.path.join(folder_name, filename)
                            try:
                                os.remove(file_path)
                            except:
                                pass

                restore_directories = [
                    (PATH_FUNCTIONS_CUSTOM, "custom_functions"),
                    (PATH_ACTIONS_CUSTOM, "custom_actions"),
                    (PATH_INPUTS_CUSTOM, "custom_inputs"),
                    (PATH_OUTPUTS_CUSTOM, "custom_outputs"),
                    (PATH_WIDGETS_CUSTOM, "custom_widgets"),
                    (PATH_USER_SCRIPTS, "user_scripts"),
                    (PATH_TEMPLATE_USER, "user_html"),
                    (PATH_PYTHON_CODE_USER, "user_python_code")
                ]

                # Restore zipped custom functions/inputs/outputs/widgets
                for each_dir in restore_directories:
                    append_to_log(IMPORT_LOG_FILE, f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Restoring {each_dir[1]} directory: {each_dir[0]}")
                    extract_dir = os.path.join(tmp_folder, each_dir[1])
                    if not os.path.exists(extract_dir):
                        continue
                    for folder_name, sub_folders, filenames in os.walk(extract_dir):
                        for filename in filenames:
                            file_path = os.path.join(folder_name, filename)
                            new_path = os.path.join(each_dir[0], filename)
                            append_to_log(IMPORT_LOG_FILE, f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Restoring {new_path}")
                            try:
                                shutil.move(file_path, new_path)
                            except:
                                append_to_log(IMPORT_LOG_FILE, f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error: Could not restore {filename}")
                                logger.exception("Moving file")

                logger.info("Finalizing import")
                import_settings_db = threading.Thread(
                    target=thread_import_settings,
                    args=(tmp_folder,))
                import_settings_db.start()

                return True
            except Exception as err:
                logger.exception("Settings import")
                error.append(f"Exception while replacing database: {err}")
                return

    except Exception as err:
        error.append("Exception: {}".format(err))

    if error:
        append_to_log(IMPORT_LOG_FILE, f"\n\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Could not complete Settings Import, error(s) found:")
    for each_err in error:
        append_to_log(IMPORT_LOG_FILE, f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error: {each_err}")

    flash_success_errors(error, action, url_for('routes_page.page_export'))
