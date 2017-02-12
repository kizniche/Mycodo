# coding=utf-8
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

from flask_influxdb import InfluxDB
influx_db = InfluxDB()
