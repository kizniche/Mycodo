# coding=utf-8
from mycodo.mycodo_flask.extensions import db
from mycodo.databases import CRUDMixin
from mycodo.databases import set_uuid


class Camera(CRUDMixin, db.Model):
    __tablename__ = "camera"

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String, nullable=False, unique=True, default=set_uuid)
    name = db.Column(db.Text, unique=True, nullable=False)
    library = db.Column(db.Text, nullable=False)
    opencv_device = db.Column(db.Integer, default=0)
    hflip = db.Column(db.Boolean, default=False)  # Horizontal flip image
    vflip = db.Column(db.Boolean, default=False)  # Vertical flip image
    rotation = db.Column(db.Integer, default=0)  # Rotation degree (0-360)
    height = db.Column(db.Integer, default=480)
    width = db.Column(db.Integer, default=640)
    brightness = db.Column(db.Float, default=None)
    contrast = db.Column(db.Float, default=None)
    exposure = db.Column(db.Float, default=None)
    gain = db.Column(db.Float, default=None)
    hue = db.Column(db.Float, default=None)
    saturation = db.Column(db.Float, default=0.3)
    white_balance = db.Column(db.Float, default=0.0)
    relay_id = db.Column(db.Integer, db.ForeignKey('relay.id'), default=None)  # Turn relay on during capture
    cmd_pre_camera = db.Column(db.Text, default='')  # Command to execute before capture
    cmd_post_camera = db.Column(db.Text, default='')  # Command to execute after capture
    stream_started = db.Column(db.Boolean, default=False)
    timelapse_started = db.Column(db.Boolean, default=False)
    timelapse_paused = db.Column(db.Boolean, default=False)
    timelapse_start_time = db.Column(db.Float, default=None)
    timelapse_end_time = db.Column(db.Float, default=None)
    timelapse_interval = db.Column(db.Float, default=None)
    timelapse_next_capture = db.Column(db.Float, default=None)
    timelapse_capture_number = db.Column(db.Integer, default=None)

    def __repr__(self):
        return "<{cls}(id={s.id}, name='{s.name}', library='{s.library}')>".format(s=self, cls=self.__class__.__name__)
