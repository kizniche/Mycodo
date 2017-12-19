# -*- coding: utf-8 -*-
import logging
import time
import zipfile

import io
import os
from flask import send_file
from flask import url_for
from flask_babel import gettext

from mycodo.config import ALEMBIC_VERSION
from mycodo.config import MYCODO_VERSION
from mycodo.config import SQL_DATABASE_MYCODO
from mycodo.mycodo_flask.utils.utils_general import flash_form_errors
from mycodo.mycodo_flask.utils.utils_general import flash_success_errors

logger = logging.getLogger(__name__)


#
# Export
#

def export_measurements(form):
    action = u'{action} {controller}'.format(
        action=gettext(u"Export"),
        controller=gettext(u"Measurements"))
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
                measurement = form.measurement.data.split(',')[1]

                url = '/export_data/{meas}/{id}/{start}/{end}'.format(
                    meas=measurement,
                    id=unique_id,
                    start=start_seconds, end=end_seconds)
                return url
        except Exception as err:
            error.append("Error: {}".format(err))
    else:
        flash_form_errors(form)
        return

    flash_success_errors(error, action, url_for('page_routes.page_export'))


def export_settings(form):
    action = u'{action} {controller}'.format(
        action=gettext(u"Export"),
        controller=gettext(u"Settings"))
    error = []

    if form.validate():
        try:
            data = io.BytesIO()
            with zipfile.ZipFile(data, mode='w') as z:
                z.write(SQL_DATABASE_MYCODO, os.path.basename(SQL_DATABASE_MYCODO))
            data.seek(0)
            return send_file(
                data,
                mimetype='application/zip',
                as_attachment=True,
                attachment_filename='Mycodo_Settings_{mver}_{aver}.zip'.format(
                    mver=MYCODO_VERSION, aver=ALEMBIC_VERSION)
            )
        except Exception as err:
            error.append("Error: {}".format(err))
    else:
        flash_form_errors(form)
        return

    flash_success_errors(error, action, url_for('page_routes.page_export'))



#
# Import
#

def import_settings(form):
    action = u'{action} {controller}'.format(
        action=gettext(u"Import"),
        controller=gettext(u"Settings"))
    error = []

    error.append('Import Settings not currently enabled')

    if form.validate():
        try:
            if not error:
                pass
        except Exception as err:
            error.append("Error: {}".format(err))
    else:
        flash_form_errors(form)
        return

    flash_success_errors(error, action, url_for('page_routes.page_export'))
