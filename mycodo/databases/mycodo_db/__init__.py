#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#  Copyright (C) 2015  Kyle T. Gabriel
#
#  This file is part of Mycodo
#
#  Mycodo is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Mycodo is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Mycodo. If not, see <http://www.gnu.org/licenses/>.
#
#  Contact at kylegabriel.com

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base, AlembicVersion, DisplayOrder, Method, Misc, CameraTimelapse, CameraStream, CameraStill, SMTP, Remote


def insert_or_ignore(an_object, a_session):
    """
    Duplicates INSERT OR IGNORE in SQLite.   This mostly illustrative and may not be production ready
    """

    a_session.add(an_object)

    try:
        a_session.commit()
    except sqlalchemy.exc.IntegrityError as e:
        # Ignore duplicate primary key
        # This is the same as the 'INSERT OR IGNORE'
        print(e)
        a_session.rollback()
        pass
    except:
        # Something else went wrong!!
        a_session.rollback()
        raise


def init_db(db_path):
    engine = create_engine(db_path)
    Base.metadata.create_all(engine)


def drop_db(db_path):
    engine = create_engine(db_path)
    Base.metadata.drop_all(engine)


def populate_db(db_path):
    engine = create_engine(db_path)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        alembic_version = AlembicVersion(version_num='2445c9b1bf3a')
        insert_or_ignore(alembic_version, session)

        initial_displayorder = DisplayOrder(id='0',
                                            graph='',
                                            log='',
                                            pid='',
                                            relay='',
                                            sensor='')
        insert_or_ignore(initial_displayorder, session)

        initial_cameratimelapse = CameraTimelapse(id='0',
                                                  relay_id='',
                                                  path='/var/www/mycodo/camera-timelapse',
                                                  prefix='Timelapse',
                                                  file_timestamp=1,
                                                  display_last=1,
                                                  cmd_pre_camera='',
                                                  cmd_post_camera='',
                                                  extra_parameters='--nopreview --contrast 20 --sharpness 60 --awb auto --quality 20 --vflip --hflip --width 800 --height 600')
        insert_or_ignore(initial_cameratimelapse, session)

        initial_camerastill = CameraStill(id='0',
                                          hflip=False,
                                          vflip=False,
                                          rotation=0,
                                          relay_id='',
                                          timestamp=1,
                                          display_last=1,
                                          cmd_pre_camera='',
                                          cmd_post_camera='',
                                          extra_parameters='--vflip --hflip --width 800 --height 600')
        insert_or_ignore(initial_camerastill, session)

        initial_camerastream = CameraStream(id='0',
                                            relay_id='',
                                            cmd_pre_camera='',
                                            cmd_post_camera='',
                                            extra_parameters='--contrast 20 --sharpness 60 --awb auto --quality 20 --vflip --hflip --nopreview --width 800 --height 600')
        insert_or_ignore(initial_camerastream, session)

        initial_misc = Misc(id='0',
                            force_https=True,
                            dismiss_notification=0,
                            hide_alert_success=False,
                            hide_alert_info=False,
                            hide_alert_warning=False,
                            stats_opt_out=False,
                            login_message='',
                            relay_stats_volts=120,
                            relay_stats_cost=0.05,
                            relay_stats_currency="$",
                            relay_stats_dayofmonth=15)
        insert_or_ignore(initial_misc, session)

        initial_smtp_values = SMTP(id='0',
                                   host='smtp.gmail.com',
                                   ssl=1,
                                   port=465,
                                   user='email@gmail.com',
                                   passw='password',
                                   email_from='email@gmail.com',
                                   hourly_max=2)
        insert_or_ignore(initial_smtp_values, session)
    finally:
        session.close()
