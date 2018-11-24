# -*- coding: utf-8 -*-
import datetime
import logging
import socket
import time
import zipfile

import io
import os
import shutil
from flask import send_file
from flask import url_for
from flask_babel import gettext
from werkzeug.utils import secure_filename

from mycodo.config import ALEMBIC_VERSION
from mycodo.config import INSTALL_DIRECTORY
from mycodo.config import MYCODO_VERSION
from mycodo.config import SQL_DATABASE_MYCODO
from mycodo.mycodo_flask.utils.utils_general import flash_form_errors
from mycodo.mycodo_flask.utils.utils_general import flash_success_errors
from mycodo.utils.system_pi import assure_path_exists
from mycodo.utils.system_pi import cmd_output

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
        action=gettext("Export"),
        controller=gettext("Measurements"))
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


def export_settings(form):
    """
    Save the Mycodo settings database (mycodo.db) to a zip file and serve it
    to the user
    """
    action = '{action} {controller}'.format(
        action=gettext("Export"),
        controller=gettext("Settings"))
    error = []

    try:
        data = io.BytesIO()
        with zipfile.ZipFile(data, mode='w') as z:
            z.write(SQL_DATABASE_MYCODO,
                    os.path.basename(SQL_DATABASE_MYCODO))
        data.seek(0)
        return send_file(
            data,
            mimetype='application/zip',
            as_attachment=True,
            attachment_filename=
                'Mycodo_{mver}_Settings_{aver}_{host}_{dt}.zip'.format(
                    mver=MYCODO_VERSION, aver=ALEMBIC_VERSION,
                    host=socket.gethostname().replace(' ', ''),
                    dt=datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        )
    except Exception as err:
        error.append("Error: {}".format(err))

    flash_success_errors(error, action, url_for('routes_page.page_export'))


def export_influxdb(form):
    """
    Save the InfluxDB metastore and mycodo_db database to a zip file and serve
    it to the user
    """
    action = '{action} {controller}'.format(
        action=gettext("Export"),
        controller=gettext("Measurements"))
    error = []

    try:
        influx_backup_dir = os.path.join(INSTALL_DIRECTORY, 'influx_backup')

        # Delete influxdb directory if it exists
        if os.path.isdir(influx_backup_dir):
            shutil.rmtree(influx_backup_dir)

        # Create new directory (make sure it's empty)
        assure_path_exists(influx_backup_dir)

        cmd = "/usr/bin/influxd backup -database mycodo_db {path}".format(
            path=influx_backup_dir)
        _, _, status = cmd_output(cmd)

        influxd_version_out, _, _ = cmd_output(
            '/usr/bin/influxd version')
        if influxd_version_out:
            influxd_version = influxd_version_out.decode('utf-8').split(' ')[1]
        else:
            influxd_version = None
            error.append("Could not determine Influxdb version")

        if not status and influxd_version:
            # Zip all files in the influx_backup directory
            data = io.BytesIO()
            with zipfile.ZipFile(data, mode='w') as z:
                for root, dirs, files in os.walk(influx_backup_dir):
                    for filename in files:
                        z.write(os.path.join(influx_backup_dir, filename),
                                filename)
            data.seek(0)

            # Delete influxdb directory if it exists
            if os.path.isdir(influx_backup_dir):
                shutil.rmtree(influx_backup_dir)

            # Send zip file to user
            return send_file(
                data,
                mimetype='application/zip',
                as_attachment=True,
                attachment_filename=
                    'Mycodo_{mv}_Influxdb_{iv}_{host}_{dt}.zip'.format(
                        mv=MYCODO_VERSION, iv=influxd_version,
                        host=socket.gethostname().replace(' ', ''),
                        dt=datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
            )
    except Exception as err:
        error.append("Error: {}".format(err))

    flash_success_errors(error, action, url_for('routes_page.page_export'))


#
# Import
#

def import_settings(form):
    """
    Receive a zip file containing a Mycodo settings database that was
    exported with export_settings(), then back up the current Mycodo settings
    database and implement the one form the zip in its's place.
    """
    action = '{action} {controller}'.format(
        action=gettext("Import"),
        controller=gettext("Settings"))
    error = []

    try:
        correct_format = 'Mycodo_MYCODOVERSION_Settings_DBVERSION_HOST_DATETIME.zip'
        upload_folder = os.path.join(INSTALL_DIRECTORY, 'upload')
        tmp_folder = os.path.join(upload_folder, 'mycodo_db_tmp')
        mycodo_database_name = 'mycodo.db'
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
                elif name_split[1] != MYCODO_VERSION:
                    error.append("Invalid Mycodo version: {fv} != {mv}. "
                                 "This database can only be imported to "
                                 "Mycodo version {mver}".format(
                        fv=name_split[1],
                        mv=MYCODO_VERSION,
                        mver=name_split[1]))
                elif name_split[3] != ALEMBIC_VERSION:
                    error.append("Invalid database version: {fv} != {dv}."
                                 " This database can only be imported to"
                                 " Mycodo version {mver}".format(
                        fv=name_split[3],
                        dv=ALEMBIC_VERSION,
                        mver=name_split[1]))
            except Exception as err:
                error.append(
                    "Exception while verifying file name: {err}".format(err=err))

        if not error:
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
                if len(file_list) > 1:
                    error.append("Incorrect number of files in zip: "
                                 "{an} != 1".format(an=len(file_list)))
                elif file_list[0] != mycodo_database_name:
                    error.append("Incorrect file in zip: {af} != {cf}".format(
                        af=file_list[0], cf=mycodo_database_name))
            except Exception as err:
                error.append("Exception while opening zip file: "
                             "{err}".format(err=err))

        if not error:
            # Unzip file
            try:
                zip_ref = zipfile.ZipFile(full_path, 'r')
                zip_ref.extractall(tmp_folder)
                zip_ref.close()
            except Exception as err:
                error.append("Exception while extracting zip file: "
                             "{err}".format(err=err))

        if not error:
            try:
                # Stop Mycodo daemon (backend)
                cmd = "{pth}/mycodo/scripts/mycodo_wrapper " \
                      "daemon_stop".format(
                    pth=INSTALL_DIRECTORY)
                out, _, _ = cmd_output(cmd)

                # Backup current database and replace with extracted mycodo.db
                imported_database = os.path.join(
                    tmp_folder, mycodo_database_name)
                backup_name = (
                        SQL_DATABASE_MYCODO + '.backup_' +
                        datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
                os.rename(SQL_DATABASE_MYCODO, backup_name)
                os.rename(imported_database, SQL_DATABASE_MYCODO)

                # Start Mycodo daemon (backend)
                cmd = "{pth}/mycodo/scripts/mycodo_wrapper " \
                      "daemon_start".format(
                    pth=INSTALL_DIRECTORY)
                out, _, _ = cmd_output(cmd)

                # Delete tmp directory if it exists
                if os.path.isdir(tmp_folder):
                    shutil.rmtree(tmp_folder)

                return backup_name  # Success!
            except Exception as err:
                error.append("Exception while replacing database: "
                             "{err}".format(err=err))

    except Exception as err:
        error.append("Exception: {}".format(err))

    flash_success_errors(error, action, url_for('routes_page.page_export'))


def import_influxdb(form):
    """
    Receive a zip file contatining influx metastore and database that was
    exported with export_influxdb(), then import the metastore and database
    in InfluxDB.
    """
    action = '{action} {controller}'.format(
        action=gettext("Import"),
        controller=gettext("Influxdb"))
    error = []

    try:
        correct_format = 'Mycodo_MYCODOVERSION_Influxdb_INFLUXVERSION_HOST_DATETIME.zip'
        upload_folder = os.path.join(INSTALL_DIRECTORY, 'upload')
        tmp_folder = os.path.join(upload_folder, 'mycodo_influx_tmp')
        full_path = None

        if not form.influxdb_import_file.data:
            error.append('No file present')
        elif form.influxdb_import_file.data.filename == '':
            error.append('No file name')
        else:
            # Split the uploaded file into parts
            file_name = form.influxdb_import_file.data.filename
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
            except Exception as err:
                error.append(
                    "Exception while verifying file name: "
                    "{err}".format(err=err))

        if not error:
            # Save file to upload directory
            filename = secure_filename(
                form.influxdb_import_file.data.filename)
            full_path = os.path.join(tmp_folder, filename)
            assure_path_exists(tmp_folder)
            assure_path_exists(tmp_folder)
            form.influxdb_import_file.data.save(
                os.path.join(tmp_folder, filename))

            # Check if contents of zip file are correct
            try:
                file_list = zipfile.ZipFile(full_path, 'r').namelist()
                if not any("meta." in s for s in file_list):
                    error.append(
                        "Metastore not found: No 'meta.*' files found "
                        "in archive")
                elif not any("mycodo_db.autogen." in s for s in file_list):
                    error.append(
                        "Databases not found: No 'mycodo_db.autogen.*' "
                        "files found in archive")
            except Exception as err:
                error.append("Exception while opening zip file: "
                             "{err}".format(err=err))

        if not error:
            # Unzip file
            try:
                zip_ref = zipfile.ZipFile(full_path, 'r')
                zip_ref.extractall(tmp_folder)
                zip_ref.close()
            except Exception as err:
                error.append("Exception while extracting zip file: "
                             "{err}".format(err=err))

        if not error:
            try:
                # Stop influxdb and Mycodo daemon (backend) from
                # running (influxdb must be stopped to restore database)
                cmd = "{pth}/mycodo/scripts/mycodo_wrapper " \
                      "daemon_stop".format(
                    pth=INSTALL_DIRECTORY)
                out, _, _ = cmd_output(cmd)

                cmd = "{pth}/mycodo/scripts/mycodo_wrapper " \
                      "influxdb_stop".format(
                    pth=INSTALL_DIRECTORY)
                out, _, _ = cmd_output(cmd)

                # Import the mestastore and database
                output_successes = []
                cmd = "{pth}/mycodo/scripts/mycodo_wrapper " \
                      "influxdb_restore_metastore {dir}".format(
                    pth=INSTALL_DIRECTORY, dir=tmp_folder)
                out, _, _ = cmd_output(cmd)
                if out:
                    output_successes.append(out.decode('utf-8'))

                cmd = "{pth}/mycodo/scripts/mycodo_wrapper " \
                      "influxdb_restore_database {dir}".format(
                    pth=INSTALL_DIRECTORY, dir=tmp_folder)
                out, _, _ = cmd_output(cmd)
                if out:
                    output_successes.append(out.decode('utf-8'))

                # Start influxdb and Mycodo daemon (backend)
                cmd = "{pth}/mycodo/scripts/mycodo_wrapper " \
                      "influxdb_start".format(
                    pth=INSTALL_DIRECTORY)
                out, _, _ = cmd_output(cmd)

                time.sleep(2)

                cmd = "{pth}/mycodo/scripts/mycodo_wrapper " \
                      "daemon_start".format(
                    pth=INSTALL_DIRECTORY)
                out, _, _ = cmd_output(cmd)

                # Delete tmp directory if it exists
                if os.path.isdir(tmp_folder):
                    shutil.rmtree(tmp_folder)

                if all(output_successes):  # Success!
                    output_successes.append(
                        "InfluxDB metastore and database successfully "
                        "imported")
                    return output_successes
            except Exception as err:
                error.append(
                    "Exception while importing metastore and database: "
                    "{err}".format(err=err))

    except Exception as err:
        error.append("Exception: {}".format(err))

    flash_success_errors(error, action, url_for('routes_page.page_export'))
