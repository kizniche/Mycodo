# coding=utf-8
from mycodo.databases import CRUDMixin
from mycodo.databases import set_uuid
from mycodo.mycodo_flask.extensions import db


class Actions(CRUDMixin, db.Model):
    __tablename__ = "conditional_data"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String, nullable=False, unique=True, default=set_uuid)
    function_id = db.Column(db.String, db.ForeignKey('conditional.unique_id'), default=None)
    function_type = db.Column(db.Text, default='')
    action_type = db.Column(db.Text, default='')  # what action, such as 'email', 'execute command', 'flash LCD'

    # Actions
    do_unique_id = db.Column(db.Text, default='')
    do_action_string = db.Column(db.Text, default='')  # string, such as the email address or command
    do_output_state = db.Column(db.Text, default='')  # 'on' or 'off'
    do_output_duration = db.Column(db.Float, default=0.0)
    do_output_pwm = db.Column(db.Float, default=0.0)
    do_camera_duration = db.Column(db.Float, default=0.0)

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)
