#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#  update-database.py - Create and update Mycodo SQLite databases
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

from .models import Base, Misc, CameraTimelapse, CameraStream, CameraStill, SMTP, CustomGraph


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
        initial_cameratimelapse = CameraTimelapse(id='0',
                                                  relay=0,
                                                  path='/var/www/mycodo/camera-timelapse',
                                                  prefix='Timelapse',
                                                  file_timestamp=1,
                                                  display_last=1,
                                                  cmd_pre='',
                                                  cmd_post='',
                                                  extra_parameters='--nopreview --contrast 20 --sharpness 60 --awb auto --quality 20 --vflip --hflip --width 800 --height 600')
        insert_or_ignore(initial_cameratimelapse, session)

        initial_camerastill = CameraStill(id='0',
                                          relay=0,
                                          timestamp=1,
                                          display_last=1,
                                          cmd_pre='',
                                          cmd_post='',
                                          extra_parameters='--vflip --hflip --width 800 --height 600')
        insert_or_ignore(initial_camerastill, session)

        initial_camerastream = CameraStream(id='0',
                                            relay=0,
                                            cmd_pre='',
                                            cmd_post='',
                                            extra_parameters='--contrast 20 --sharpness 60 --awb auto --quality 20 --vflip --hflip --nopreview --width 800 --height 600')
        insert_or_ignore(initial_camerastream, session)

        initial_customgraph = CustomGraph(id='0',
                                          combined_temp_min=0,
                                          combined_temp_max=35,
                                          combined_temp_tics=5,
                                          combined_temp_mtics=5,
                                          combined_temp_relays_up='0',
                                          combined_temp_relays_down='0',
                                          combined_temp_relays_min=-100,
                                          combined_temp_relays_max=100,
                                          combined_temp_relays_tics=25,
                                          combined_temp_relays_mtics=5,
                                          combined_hum_min=0,
                                          combined_hum_max=100,
                                          combined_hum_tics=10,
                                          combined_hum_mtics=5,
                                          combined_hum_relays_up='0',
                                          combined_hum_relays_down='0',
                                          combined_hum_relays_min=-100,
                                          combined_hum_relays_max=100,
                                          combined_hum_relays_tics=25,
                                          combined_hum_relays_mtics=5,
                                          combined_co2_min=0,
                                          combined_co2_max=5000,
                                          combined_co2_tics=500,
                                          combined_co2_mtics=5,
                                          combined_co2_relays_up='0',
                                          combined_co2_relays_down='0',
                                          combined_co2_relays_min=-100,
                                          combined_co2_relays_max=100,
                                          combined_co2_relays_tics=25,
                                          combined_co2_relays_mtics=5,
                                          combined_press_min=96000,
                                          combined_press_max=100000,
                                          combined_press_tics=500,
                                          combined_press_mtics=5,
                                          combined_press_relays_up='0',
                                          combined_press_relays_down='0',
                                          combined_press_relays_min=-100,
                                          combined_press_relays_max=100,
                                          combined_press_relays_tics=25,
                                          combined_press_relays_mtics=5)
        insert_or_ignore(initial_customgraph, session)

        initial_misc = Misc(id='0',
                            dismiss_notification=0,
                            login_message='',
                            refresh_time=300,
                            enable_max_amps=1,
                            max_amps=15,
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
                                   daily_max=48,
                                   wait_time=3600)
        insert_or_ignore(initial_smtp_values, session)
    finally:
        session.close()
