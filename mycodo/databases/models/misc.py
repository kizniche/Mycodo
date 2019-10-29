# coding=utf-8
from mycodo.databases import CRUDMixin
from mycodo.databases import set_uuid
from mycodo.mycodo_flask.extensions import db


class Misc(CRUDMixin, db.Model):
    __tablename__ = "misc"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    dismiss_notification = db.Column(db.Boolean, default=False)  # Dismiss login page license notice
    force_https = db.Column(db.Boolean, default=True)  # Force web interface to use SSL/HTTPS
    hide_alert_info = db.Column(db.Boolean, default=False)
    hide_alert_success = db.Column(db.Boolean, default=False)
    hide_alert_warning = db.Column(db.Boolean, default=False)
    hide_tooltips = db.Column(db.Boolean, default=False)
    login_message = db.Column(db.Text, default='')  # Put a message on the login screen
    max_amps = db.Column(db.Float, default=15.0)  # Maximum allowed current to be drawn
    output_usage_cost = db.Column(db.Float, default=0.05)  # Energy cost per kWh
    output_usage_currency = db.Column(db.Text, default='$')  # Energy cost currency
    output_usage_dayofmonth = db.Column(db.Integer, default=15)  # Electricity billing day of month
    output_usage_volts = db.Column(db.Integer, default=120)  # Voltage the alternating current operates
    output_usage_report_gen = db.Column(db.Boolean, default=False)
    output_usage_report_span = db.Column(db.Text, default='monthly')
    output_usage_report_day = db.Column(db.Integer, default=1)
    output_usage_report_hour = db.Column(db.Integer, default=0)
    sample_rate_controller_conditional = db.Column(db.Float, default=0.25)
    sample_rate_controller_input = db.Column(db.Float, default=0.1)
    sample_rate_controller_math = db.Column(db.Float, default=0.25)
    sample_rate_controller_output = db.Column(db.Float, default=0.05)
    sample_rate_controller_pid = db.Column(db.Float, default=0.1)
    stats_opt_out = db.Column(db.Boolean, default=False)  # Opt not to send anonymous usage statistics
    enable_upgrade_check = db.Column(db.Boolean, default=True)  # Periodically check for a Mycodo upgrade
    mycodo_upgrade_available = db.Column(db.Boolean, default=False)  # Stores if an upgrade is available
    rpyc_timeout = db.Column(db.Integer, default=30)
    daemon_debug_mode = db.Column(db.Boolean, default=False)
    net_test_ip = db.Column(db.String, default='8.8.8.8')
    net_test_port = db.Column(db.Integer, default=53)
    net_test_timeout = db.Column(db.Integer, default=3)

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)


class EnergyUsage(CRUDMixin, db.Model):
    __tablename__ = "energy_usage"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String, nullable=False, unique=True, default=set_uuid)  # ID for influxdb entries
    name = db.Column(db.Text, default='Name')
    device_id = db.Column(db.Text, default='')
    measurement_id = db.Column(db.Text, db.ForeignKey('device_measurements.unique_id'), default='')
