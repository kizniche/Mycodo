# coding=utf-8
from mycodo.databases import CRUDMixin
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
    relay_usage_cost = db.Column(db.Float, default=0.05)  # Energy cost per kWh
    relay_usage_currency = db.Column(db.Text, default='$')  # Energy cost currency
    relay_usage_dayofmonth = db.Column(db.Integer, default=15)  # Electricity billing day of month
    relay_usage_volts = db.Column(db.Integer, default=120)  # Voltage the alternating current operates
    relay_usage_report_gen = db.Column(db.Boolean, default=False)
    relay_usage_report_span = db.Column(db.Text, default='monthly')
    relay_usage_report_day = db.Column(db.Integer, default=1)
    relay_usage_report_hour = db.Column(db.Integer, default=0)
    stats_opt_out = db.Column(db.Boolean, default=False)  # Opt not to send anonymous usage statistics
    enable_upgrade_check = db.Column(db.Boolean, default=True)  # Periodically check for a Mycodo upgrade
    mycodo_upgrade_available = db.Column(db.Boolean, default=False)  # Stores if an upgrade is available

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)
