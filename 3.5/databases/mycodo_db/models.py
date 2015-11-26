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

from sqlalchemy import Column, TEXT, INT, REAL
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Relays(Base):
    __tablename__ = "relays"

    id = Column(TEXT, unique=True, primary_key=True)
    name = Column(TEXT)
    pin = Column(INT)
    amps = Column(REAL)
    trigger = Column(INT)
    start_state = Column(INT)


class RelayConditional(Base):
    __tablename__ = "relayconditional"

    id = Column(TEXT, unique=True, primary_key=True)
    name = Column(TEXT)
    if_relay = Column(INT)
    if_action = Column(TEXT)
    if_duration = Column(REAL)
    sel_relay = Column(INT)
    do_relay = Column(INT)
    do_action = Column(TEXT)
    do_duration = Column(REAL)
    sel_command = Column(INT)
    do_command = Column(TEXT)
    sel_notify = Column(INT)
    do_notify = Column(TEXT)


class TSensor(Base):
    __tablename__ = "tsensor"

    id = Column(TEXT, unique=True, primary_key=True)
    name = Column(TEXT)
    pin = Column(TEXT)
    device = Column(TEXT)
    period = Column(INT)
    pre_measure_relay = Column(INT)
    pre_measure_dur = Column(INT)
    activated = Column(INT)
    graph = Column(INT)
    yaxis_relay_min = Column(INT)
    yaxis_relay_max = Column(INT)
    yaxis_relay_tics = Column(INT)
    yaxis_relay_mtics = Column(INT)
    yaxis_temp_min = Column(INT)
    yaxis_temp_max = Column(INT)
    yaxis_temp_tics = Column(INT)
    yaxis_temp_mtics = Column(INT)
    temp_relays_up = Column(TEXT)
    temp_relays_down = Column(TEXT)
    temp_relay_high = Column(INT)
    temp_outmin_high = Column(INT)
    temp_outmax_high = Column(INT)
    temp_relay_low = Column(INT)
    temp_outmin_low = Column(INT)
    temp_outmax_low = Column(INT)
    temp_or = Column(INT)
    temp_set = Column(REAL)
    temp_set_direction = Column(INT)
    temp_period = Column(INT)
    temp_p = Column(REAL)
    temp_i = Column(REAL)
    temp_d = Column(REAL)


class TSensorPreset(Base):
    __tablename__ = "tsensorpreset"

    id = Column(TEXT, unique=True, primary_key=True)
    name = Column(TEXT)
    pin = Column(TEXT)
    device = Column(TEXT)
    period = Column(INT)
    pre_measure_relay = Column(INT)
    pre_measure_dur = Column(INT)
    activated = Column(INT)
    graph = Column(INT)
    yaxis_relay_min = Column(INT)
    yaxis_relay_max = Column(INT)
    yaxis_relay_tics = Column(INT)
    yaxis_relay_mtics = Column(INT)
    yaxis_temp_min = Column(INT)
    yaxis_temp_max = Column(INT)
    yaxis_temp_tics = Column(INT)
    yaxis_temp_mtics = Column(INT)
    temp_relays_up = Column(TEXT)
    temp_relays_down = Column(TEXT)
    temp_relay_high = Column(INT)
    temp_outmin_high = Column(INT)
    temp_outmax_high = Column(INT)
    temp_relay_low = Column(INT)
    temp_outmin_low = Column(INT)
    temp_outmax_low = Column(INT)
    temp_set = Column(REAL)
    temp_set_direction = Column(INT)
    temp_period = Column(INT)
    temp_p = Column(REAL)
    temp_i = Column(REAL)
    temp_d = Column(REAL)


class TSensorConditional(Base):
    __tablename__ = "tsensorconditional"

    id = Column(TEXT, unique=True, primary_key=True)
    name = Column(TEXT)
    state = Column(INT)
    sensor = Column(INT)
    direction = Column(INT)
    setpoint = Column(REAL)
    period = Column(INT)
    sel_relay = Column(INT)
    relay = Column(INT)
    relay_state = Column(INT)
    relay_seconds_on = Column(INT)
    sel_command = Column(INT)
    do_command = Column(TEXT)
    sel_notify = Column(INT)
    do_notify = Column(TEXT)


class HTSensor(Base):
    __tablename__ = "htsensor"

    id = Column(TEXT, unique=True, primary_key=True)
    name = Column(TEXT)
    pin = Column(INT)
    device = Column(TEXT)
    period = Column(INT)
    pre_measure_relay = Column(INT)
    pre_measure_dur = Column(INT)
    activated = Column(INT)
    graph = Column(INT)
    verify_pin = Column(INT)
    verify_temp = Column(REAL)
    verify_temp_notify = Column(INT)
    verify_temp_stop = Column(INT)
    verify_hum = Column(REAL)
    verify_hum_notify = Column(INT)
    verify_hum_stop = Column(INT)
    verify_notify_email = Column(TEXT)
    yaxis_relay_min = Column(INT)
    yaxis_relay_max = Column(INT)
    yaxis_relay_tics = Column(INT)
    yaxis_relay_mtics = Column(INT)
    yaxis_temp_min = Column(INT)
    yaxis_temp_max = Column(INT)
    yaxis_temp_tics = Column(INT)
    yaxis_temp_mtics = Column(INT)
    yaxis_hum_min = Column(INT)
    yaxis_hum_max = Column(INT)
    yaxis_hum_tics = Column(INT)
    yaxis_hum_mtics = Column(INT)
    temp_relays_up = Column(TEXT)
    temp_relays_down = Column(TEXT)
    temp_relay_high = Column(INT)
    temp_outmin_high = Column(INT)
    temp_outmax_high = Column(INT)
    temp_relay_low = Column(INT)
    temp_outmin_low = Column(INT)
    temp_outmax_low = Column(INT)
    temp_or = Column(INT)
    temp_set = Column(REAL)
    temp_set_direction = Column(INT)
    temp_period = Column(INT)
    temp_p = Column(REAL)
    temp_i = Column(REAL)
    temp_d = Column(REAL)
    hum_relays_up = Column(TEXT)
    hum_relays_down = Column(TEXT)
    hum_relay_high = Column(INT)
    hum_outmin_high = Column(INT)
    hum_outmax_high = Column(INT)
    hum_relay_low = Column(INT)
    hum_outmin_low = Column(INT)
    hum_outmax_low = Column(INT)
    hum_or = Column(INT)
    hum_set = Column(REAL)
    hum_set_direction = Column(INT)
    hum_period = Column(INT)
    hum_p = Column(REAL)
    hum_i = Column(REAL)
    hum_d = Column(REAL)


class HTSensorPreset(Base):
    __tablename__ = "htsensorpreset"

    id = Column(TEXT, unique=True, primary_key=True)
    name = Column(TEXT)
    pin = Column(INT)
    device = Column(TEXT)
    period = Column(INT)
    pre_measure_relay = Column(INT)
    pre_measure_dur = Column(INT)
    activated = Column(INT)
    graph = Column(INT)
    verify_pin = Column(INT)
    verify_temp = Column(REAL)
    verify_temp_notify = Column(INT)
    verify_temp_stop = Column(INT)
    verify_hum = Column(REAL)
    verify_hum_notify = Column(INT)
    verify_hum_stop = Column(INT)
    verify_notify_email = Column(TEXT)
    yaxis_relay_min = Column(INT)
    yaxis_relay_max = Column(INT)
    yaxis_relay_tics = Column(INT)
    yaxis_relay_mtics = Column(INT)
    yaxis_temp_min = Column(INT)
    yaxis_temp_max = Column(INT)
    yaxis_temp_tics = Column(INT)
    yaxis_temp_mtics = Column(INT)
    yaxis_hum_min = Column(INT)
    yaxis_hum_max = Column(INT)
    yaxis_hum_tics = Column(INT)
    yaxis_hum_mtics = Column(INT)
    temp_relays_up = Column(TEXT)
    temp_relays_down = Column(TEXT)
    temp_relay_high = Column(INT)
    temp_outmin_high = Column(INT)
    temp_outmax_high = Column(INT)
    temp_relay_low = Column(INT)
    temp_outmin_low = Column(INT)
    temp_outmax_low = Column(INT)
    temp_set = Column(REAL)
    temp_set_direction = Column(INT)
    temp_period = Column(INT)
    temp_p = Column(REAL)
    temp_i = Column(REAL)
    temp_d = Column(REAL)
    hum_relays_up = Column(TEXT)
    hum_relays_down = Column(TEXT)
    hum_relay_high = Column(INT)
    hum_outmin_high = Column(INT)
    hum_outmax_high = Column(INT)
    hum_relay_low = Column(INT)
    hum_outmin_low = Column(INT)
    hum_outmax_low = Column(INT)
    hum_set = Column(REAL)
    hum_set_direction = Column(INT)
    hum_period = Column(INT)
    hum_p = Column(REAL)
    hum_i = Column(REAL)
    hum_d = Column(REAL)


class HTSensorConditional(Base):
    __tablename__ = "htsensorconditional"

    id = Column(TEXT, unique=True, primary_key=True)
    name = Column(TEXT)
    state = Column(INT)
    sensor = Column(INT)
    condition = Column(TEXT)
    direction = Column(INT)
    setpoint = Column(REAL)
    period = Column(INT)
    sel_relay = Column(INT)
    relay = Column(INT)
    relay_state = Column(INT)
    relay_seconds_on = Column(INT)
    sel_command = Column(INT)
    do_command = Column(TEXT)
    sel_notify = Column(INT)
    do_notify = Column(TEXT)


class CO2Sensor(Base):
    __tablename__ = "co2sensor"

    id = Column(TEXT, unique=True, primary_key=True)
    name = Column(TEXT)
    pin = Column(INT)
    device = Column(TEXT)
    period = Column(INT)
    pre_measure_relay = Column(INT)
    pre_measure_dur = Column(INT)
    activated = Column(INT)
    graph = Column(INT)
    yaxis_relay_min = Column(INT)
    yaxis_relay_max = Column(INT)
    yaxis_relay_tics = Column(INT)
    yaxis_relay_mtics = Column(INT)
    yaxis_co2_min = Column(INT)
    yaxis_co2_max = Column(INT)
    yaxis_co2_tics = Column(INT)
    yaxis_co2_mtics = Column(INT)
    co2_relays_up = Column(TEXT)
    co2_relays_down = Column(TEXT)
    co2_relay_high = Column(INT)
    co2_outmin_high = Column(INT)
    co2_outmax_high = Column(INT)
    co2_relay_low = Column(INT)
    co2_outmin_low = Column(INT)
    co2_outmax_low = Column(INT)
    co2_or = Column(INT)
    co2_set = Column(REAL)
    co2_set_direction = Column(INT)
    co2_period = Column(INT)
    co2_p = Column(REAL)
    co2_i = Column(REAL)
    co2_d = Column(REAL)


class CO2SensorPreset(Base):
    __tablename__ = "co2sensorpreset"

    id = Column(TEXT, unique=True, primary_key=True)
    name = Column(TEXT)
    pin = Column(INT)
    device = Column(TEXT)
    period = Column(INT)
    pre_measure_relay = Column(INT)
    pre_measure_dur = Column(INT)
    activated = Column(INT)
    graph = Column(INT)
    yaxis_relay_min = Column(INT)
    yaxis_relay_max = Column(INT)
    yaxis_relay_tics = Column(INT)
    yaxis_relay_mtics = Column(INT)
    yaxis_co2_min = Column(INT)
    yaxis_co2_max = Column(INT)
    yaxis_co2_tics = Column(INT)
    yaxis_co2_mtics = Column(INT)
    co2_relays_up = Column(TEXT)
    co2_relays_down = Column(TEXT)
    co2_relay_high = Column(INT)
    co2_outmin_high = Column(INT)
    co2_outmax_high = Column(INT)
    co2_relay_low = Column(INT)
    co2_outmin_low = Column(INT)
    co2_outmax_low = Column(INT)
    co2_set = Column(REAL)
    co2_set_direction = Column(INT)
    co2_period = Column(INT)
    co2_p = Column(REAL)
    co2_i = Column(REAL)
    co2_d = Column(REAL)


class CO2SensorConditional(Base):
    __tablename__ = "co2sensorconditional"

    id = Column(TEXT, unique=True, primary_key=True)
    name = Column(TEXT)
    state = Column(INT)
    sensor = Column(INT)
    direction = Column(INT)
    setpoint = Column(REAL)
    period = Column(INT)
    sel_relay = Column(INT)
    relay = Column(INT)
    relay_state = Column(INT)
    relay_seconds_on = Column(INT)
    sel_command = Column(INT)
    do_command = Column(TEXT)
    sel_notify = Column(INT)
    do_notify = Column(TEXT)


class PressSensor(Base):
    __tablename__ = "presssensor"

    id = Column(TEXT, unique=True, primary_key=True)
    name = Column(TEXT)
    pin = Column(INT)
    device = Column(TEXT)
    period = Column(INT)
    pre_measure_relay = Column(INT)
    pre_measure_dur = Column(INT)
    activated = Column(INT)
    graph = Column(INT)
    yaxis_relay_min = Column(INT)
    yaxis_relay_max = Column(INT)
    yaxis_relay_tics = Column(INT)
    yaxis_relay_mtics = Column(INT)
    yaxis_temp_min = Column(INT)
    yaxis_temp_max = Column(INT)
    yaxis_temp_tics = Column(INT)
    yaxis_temp_mtics = Column(INT)
    yaxis_press_min = Column(INT)
    yaxis_press_max = Column(INT)
    yaxis_press_tics = Column(INT)
    yaxis_press_mtics = Column(INT)
    temp_relays_up = Column(TEXT)
    temp_relays_down = Column(TEXT)
    temp_relay_high = Column(INT)
    temp_outmin_high = Column(INT)
    temp_outmax_high = Column(INT)
    temp_relay_low = Column(INT)
    temp_outmin_low = Column(INT)
    temp_outmax_low = Column(INT)
    temp_or = Column(INT)
    temp_set = Column(REAL)
    temp_set_direction = Column(INT)
    temp_period = Column(INT)
    temp_p = Column(REAL)
    temp_i = Column(REAL)
    temp_d = Column(REAL)
    press_relays_up = Column(TEXT)
    press_relays_down = Column(TEXT)
    press_relay_high = Column(INT)
    press_outmin_high = Column(INT)
    press_outmax_high = Column(INT)
    press_relay_low = Column(INT)
    press_outmin_low = Column(INT)
    press_outmax_low = Column(INT)
    press_or = Column(INT)
    press_set = Column(REAL)
    press_set_direction = Column(INT)
    press_period = Column(INT)
    press_p = Column(REAL)
    press_i = Column(REAL)
    press_d = Column(REAL)


class PressSensorPreset(Base):
    __tablename__ = "presssensorpreset"

    id = Column(TEXT, unique=True, primary_key=True)
    name = Column(TEXT)
    pin = Column(INT)
    device = Column(TEXT)
    period = Column(INT)
    pre_measure_relay = Column(INT)
    pre_measure_dur = Column(INT)
    activated = Column(INT)
    graph = Column(INT)
    yaxis_relay_min = Column(INT)
    yaxis_relay_max = Column(INT)
    yaxis_relay_tics = Column(INT)
    yaxis_relay_mtics = Column(INT)
    yaxis_temp_min = Column(INT)
    yaxis_temp_max = Column(INT)
    yaxis_temp_tics = Column(INT)
    yaxis_temp_mtics = Column(INT)
    yaxis_press_min = Column(INT)
    yaxis_press_max = Column(INT)
    yaxis_press_tics = Column(INT)
    yaxis_press_mtics = Column(INT)
    temp_relays_up = Column(TEXT)
    temp_relays_down = Column(TEXT)
    temp_relay_high = Column(INT)
    temp_outmin_high = Column(INT)
    temp_outmax_high = Column(INT)
    temp_relay_low = Column(INT)
    temp_outmin_low = Column(INT)
    temp_outmax_low = Column(INT)
    temp_set = Column(REAL)
    temp_set_direction = Column(INT)
    temp_period = Column(INT)
    temp_p = Column(REAL)
    temp_i = Column(REAL)
    temp_d = Column(REAL)
    press_relays_up = Column(TEXT)
    press_relays_down = Column(TEXT)
    press_relay_high = Column(INT)
    press_outmin_high = Column(INT)
    press_outmax_high = Column(INT)
    press_relay_low = Column(INT)
    press_outmin_low = Column(INT)
    press_outmax_low = Column(INT)
    press_set = Column(REAL)
    press_set_direction = Column(INT)
    press_period = Column(INT)
    press_p = Column(REAL)
    press_i = Column(REAL)
    press_d = Column(REAL)


class PressSensorConditional(Base):
    __tablename__ = "presssensorconditional"

    id = Column(TEXT, unique=True, primary_key=True)
    name = Column(TEXT)
    state = Column(INT)
    sensor = Column(INT)
    condition = Column(TEXT)
    direction = Column(INT)
    setpoint = Column(REAL)
    period = Column(INT)
    sel_relay = Column(INT)
    relay = Column(INT)
    relay_state = Column(INT)
    relay_seconds_on = Column(INT)
    sel_command = Column(INT)
    do_command = Column(TEXT)
    sel_notify = Column(INT)
    do_notify = Column(TEXT)


class Timers(Base):
    __tablename__ = "timers"

    id = Column(TEXT, unique=True, primary_key=True)
    name = Column(TEXT)
    relay = Column(INT)
    state = Column(INT)
    durationon = Column(INT)
    durationoff = Column(INT)


class CustomGraph(Base):
    __tablename__ = "customgraph"

    id = Column(TEXT, unique=True, primary_key=True)
    combined_temp_min = Column(INT)
    combined_temp_max = Column(INT)
    combined_temp_tics = Column(INT)
    combined_temp_mtics = Column(INT)
    combined_temp_relays_up = Column(TEXT)
    combined_temp_relays_down = Column(TEXT)
    combined_temp_relays_min = Column(INT)
    combined_temp_relays_max = Column(INT)
    combined_temp_relays_tics = Column(INT)
    combined_temp_relays_mtics = Column(INT)
    combined_hum_min = Column(INT)
    combined_hum_max = Column(INT)
    combined_hum_tics = Column(INT)
    combined_hum_mtics = Column(INT)
    combined_hum_relays_up = Column(TEXT)
    combined_hum_relays_down = Column(TEXT)
    combined_hum_relays_min = Column(INT)
    combined_hum_relays_max = Column(INT)
    combined_hum_relays_tics = Column(INT)
    combined_hum_relays_mtics = Column(INT)
    combined_co2_min = Column(INT)
    combined_co2_max = Column(INT)
    combined_co2_tics = Column(INT)
    combined_co2_mtics = Column(INT)
    combined_co2_relays_up = Column(TEXT)
    combined_co2_relays_down = Column(TEXT)
    combined_co2_relays_min = Column(INT)
    combined_co2_relays_max = Column(INT)
    combined_co2_relays_tics = Column(INT)
    combined_co2_relays_mtics = Column(INT)
    combined_press_min = Column(INT)
    combined_press_max = Column(INT)
    combined_press_tics = Column(INT)
    combined_press_mtics = Column(INT)
    combined_press_relays_up = Column(TEXT)
    combined_press_relays_down = Column(TEXT)
    combined_press_relays_min = Column(INT)
    combined_press_relays_max = Column(INT)
    combined_press_relays_tics = Column(INT)
    combined_press_relays_mtics = Column(INT)


class SMTP(Base):
    __tablename__ = "smtp"

    id = Column(TEXT, unique=True, primary_key=True)
    host = Column(TEXT)
    ssl = Column(INT)
    port = Column(INT)
    user = Column(TEXT)
    passw = Column(TEXT)  # TODO:  Note that this is 'passw' and not 'pass'. 'pass' is reserved
    email_from = Column(TEXT)
    daily_max = Column(INT)
    wait_time = Column(INT)


class CameraStill(Base):
    __tablename__ = "camerastill"

    id = Column(TEXT, unique=True, primary_key=True)
    relay = Column(INT)
    timestamp = Column(INT)
    display_last = Column(INT)
    cmd_pre = Column(TEXT)
    cmd_post = Column(TEXT)
    extra_parameters = Column(TEXT)


class CameraStream(Base):
    __tablename__ = "camerastream"

    id = Column(TEXT, unique=True, primary_key=True)
    relay = Column(INT)
    cmd_pre = Column(TEXT)
    cmd_post = Column(TEXT)
    extra_parameters = Column(TEXT)


class CameraTimelapse(Base):
    __tablename__ = "cameratimelapse"

    id = Column(TEXT, unique=True, primary_key=True)
    relay = Column(INT)
    path = Column(TEXT)
    prefix = Column(TEXT)
    file_timestamp = Column(INT)
    display_last = Column(INT)
    cmd_pre = Column(TEXT)
    cmd_post = Column(TEXT)
    extra_parameters = Column(TEXT)


class Misc(Base):
    __tablename__ = "misc"

    id = Column(TEXT, unique=True, primary_key=True)
    dismiss_notification = Column(INT)
    login_message = Column(TEXT)
    refresh_time = Column(INT)
    enable_max_amps = Column(INT)
    max_amps = Column(REAL)
    relay_stats_volts = Column(INT)
    relay_stats_cost = Column(REAL)
    relay_stats_currency = Column(TEXT)
    relay_stats_dayofmonth = Column(INT)
