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
from influxdb import InfluxDBClient
from werkzeug.utils import secure_filename

from mycodo.config import (ALEMBIC_VERSION, DATABASE_NAME, DEPENDENCY_LOG_FILE,
                           DOCKER_CONTAINER, INSTALL_DIRECTORY, MYCODO_VERSION,
                           PATH_ACTIONS_CUSTOM, PATH_FUNCTIONS_CUSTOM,
                           PATH_HTML_USER, PATH_INPUTS_CUSTOM,
                           PATH_OUTPUTS_CUSTOM, PATH_PYTHON_CODE_USER,
                           PATH_USER_SCRIPTS, PATH_WIDGETS_CUSTOM,
                           SQL_DATABASE_MYCODO)
from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import Misc
from mycodo.mycodo_flask.utils.utils_general import (flash_form_errors,
                                                     flash_success_errors)
from mycodo.scripts.measurement_db import get_influxdb_info
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.system_pi import assure_path_exists, cmd_output
from mycodo.utils.tools import (create_measurements_export,
                                create_settings_export)
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
            error.append("Error: {}".format(err))
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
        error.append("Error: {}".format(err))

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
        error.append("Error: {}".format(err))

    flash_success_errors(error, action, url_for('routes_page.page_export'))


#
# Import
#

def thread_import_settings(tmp_folder):
    logger.info("Finishing up settings import")

    try:
        # Upgrade database
        cmd = "{pth}/mycodo/scripts/mycodo_wrapper " \
              "upgrade_database".format(
            pth=INSTALL_DIRECTORY)
        _, _, _ = cmd_output(cmd)

        # Install/update dependencies (could take a while)
        cmd = "{pth}/mycodo/scripts/mycodo_wrapper update_dependencies" \
              " | ts '[%Y-%m-%d %H:%M:%S]' >> {log} 2>&1".format(
            pth=INSTALL_DIRECTORY,
            log=DEPENDENCY_LOG_FILE)
        _, _, _ = cmd_output(cmd)

        # Initialize
        cmd = "{pth}/mycodo/scripts/mycodo_wrapper " \
              "initialize".format(
            pth=INSTALL_DIRECTORY)
        _, _, _ = cmd_output(cmd)

        # Generate widget HTML
        generate_widget_html()

        if DOCKER_CONTAINER:
            subprocess.Popen('docker start mycodo_daemon 2>&1', shell=True)
        else:
            # Start Mycodo daemon (backend)
            cmd = "{pth}/mycodo/scripts/mycodo_wrapper " \
                  "daemon_start".format(
                pth=INSTALL_DIRECTORY)
            _, _, _ = cmd_output(cmd)

        # Delete tmp directory if it exists
        if os.path.isdir(tmp_folder):
            shutil.rmtree(tmp_folder)
    except:
        logger.exception("thread_import_settings()")

    logger.info("Settings import complete")


def import_settings(form):
    """
    Receive a zip file containing a Mycodo settings database that was
    exported with export_settings(), then back up the current Mycodo settings
    database and implement the one form the zip in its's place.
    """
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['import']['title'],
        controller=TRANSLATIONS['settings']['title'])
    error = []

    try:
        logger.info("Beginning settings import")
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
                    error.append(
                        "Invalid file name: {n}: {fn} != {cn}.".format(
                            n=file_name,
                            fn=name_split[0],
                            cn=correct_name_1))
                    error.append("Correct format is: {fmt}".format(
                        fmt=correct_format))
                elif name_split[2] != correct_name_2:
                    error.append(
                        "Invalid file name: {n}: {fn} != {cn}".format(
                            n=file_name,
                            fn=name_split[2],
                            cn=correct_name_2))
                    error.append("Correct format is: {fmt}".format(
                        fmt=correct_format))
                elif extension != correct_extension:
                    error.append("Extension not 'zip'")
                elif name_split[1] > MYCODO_VERSION:
                    error.append(
                        "Invalid Mycodo version: {fv} > {mv}. "
                        "Only databases <= {mver} can only be imported".format(
                            fv=name_split[1],
                            mv=MYCODO_VERSION,
                            mver=name_split[1]))
            except Exception as err:
                error.append(
                    "Exception while verifying file name: {err}".format(err=err))

        if not error:
            logger.info("Saving import file")
            # Save file to upload directory
            filename = secure_filename(
                form.settings_import_file.data.filename)
            full_path = os.path.join(tmp_folder, filename)
            assure_path_exists(upload_folder)
            assure_path_exists(tmp_folder)
            form.settings_import_file.data.save(
                os.path.join(tmp_folder, filename))

            # Check if contents of zip file are correct
            try:
                file_list = zipfile.ZipFile(full_path, 'r').namelist()
                if DATABASE_NAME not in file_list:
                    error.append("{} not found in zip: {}".format(
                        DATABASE_NAME, ", ".join(file_list)))
            except Exception as err:
                error.append("Exception checking files in zip: "
                             "{err}".format(err=err))

        if not error:
            logger.info("Unzipping import file")
            # Unzip file
            try:
                assure_path_exists(tmp_folder)
                zip_ref = zipfile.ZipFile(full_path, 'r')
                zip_ref.extractall(tmp_folder)
                zip_ref.close()
            except Exception as err:
                error.append("Exception while extracting zip file: "
                             "{err}".format(err=err))

        if not error:
            logger.info("Stopping daemon and copying files")
            try:
                if DOCKER_CONTAINER:
                    subprocess.Popen('docker stop mycodo_daemon 2>&1', shell=True)
                else:
                    # Stop Mycodo daemon (backend)
                    cmd = "{pth}/mycodo/scripts/mycodo_wrapper " \
                          "daemon_stop".format(
                        pth=INSTALL_DIRECTORY)
                    _, _, _ = cmd_output(cmd)

                # Backup current database and replace with extracted mycodo.db
                imported_database = os.path.join(tmp_folder, DATABASE_NAME)
                backup_name = "{}.backup_{}".format(
                    SQL_DATABASE_MYCODO,
                    datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))

                os.rename(SQL_DATABASE_MYCODO, backup_name)  # rename current database to backup name
                shutil.move(imported_database, SQL_DATABASE_MYCODO)  # move unzipped database to Mycodo

                delete_directories = [
                    PATH_FUNCTIONS_CUSTOM,
                    PATH_ACTIONS_CUSTOM,
                    PATH_INPUTS_CUSTOM,
                    PATH_OUTPUTS_CUSTOM,
                    PATH_WIDGETS_CUSTOM,
                    PATH_HTML_USER,
                    PATH_PYTHON_CODE_USER,
                    PATH_USER_SCRIPTS
                ]

                # Delete custom functions/inputs/outputs/widgets and generated HTML/Python code
                for each_dir in delete_directories:
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
                    (PATH_USER_SCRIPTS, "user_scripts")
                ]

                # Restore zipped custom functions/inputs/outputs/widgets
                for each_dir in restore_directories:
                    extract_dir = os.path.join(tmp_folder, each_dir[1])
                    if not os.path.exists(extract_dir):
                        continue
                    for folder_name, sub_folders, filenames in os.walk(extract_dir):
                        for filename in filenames:
                            file_path = os.path.join(folder_name, filename)
                            new_path = os.path.join(each_dir[0], filename)
                            try:
                                shutil.move(file_path, new_path)
                            except:
                                logger.exception("Moving file")

                logger.info("Finalizing import")
                import_settings_db = threading.Thread(
                    target=thread_import_settings,
                    args=(tmp_folder,))
                import_settings_db.start()

                return backup_name
            except Exception as err:
                logger.exception("Settings import")
                error.append("Exception while replacing database: "
                             "{err}".format(err=err))
                return None

    except Exception as err:
        error.append("Exception: {}".format(err))

    flash_success_errors(error, action, url_for('routes_page.page_export'))
