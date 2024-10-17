# coding=utf-8
from mycodo.databases import CRUDMixin
from mycodo.databases import set_uuid
from mycodo.mycodo_flask.extensions import db


class Camera(CRUDMixin, db.Model):
    __tablename__ = "camera"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String(36), nullable=False, unique=True, default=set_uuid)
    name = db.Column(db.Text, unique=True, nullable=False)
    library = db.Column(db.Text, nullable=False)
    device = db.Column(db.Text, nullable=False, default='/dev/video0')
    opencv_device = db.Column(db.Integer, default=0)
    hflip = db.Column(db.Boolean, default=False)  # Horizontal flip image
    vflip = db.Column(db.Boolean, default=False)  # Vertical flip image
    rotation = db.Column(db.Integer, default=0)  # Rotation degree (0-360)
    brightness = db.Column(db.Float, default=0)
    contrast = db.Column(db.Float, default=0)
    exposure = db.Column(db.Float, default=None)
    gain = db.Column(db.Float, default=None)
    hue = db.Column(db.Float, default=None)
    saturation = db.Column(db.Float, default=0)
    white_balance = db.Column(db.Float, default=0.0)
    custom_options = db.Column(db.Text, default='')
    output_id = db.Column(db.String(36), default=None)  # Turn output on during capture
    output_duration = db.Column(db.Float, default=3.0)
    cmd_pre_camera = db.Column(db.Text, default='')  # Command to execute before capture
    cmd_post_camera = db.Column(db.Text, default='')  # Command to execute after capture
    stream_started = db.Column(db.Boolean, default=False)
    hide_still = db.Column(db.Boolean, default=False)
    hide_timelapse = db.Column(db.Boolean, default=False)
    url_still = db.Column(db.Text, default='')
    url_stream = db.Column(db.Text, default='')
    json_headers = db.Column(db.Text, default='')
    show_preview = db.Column(db.Boolean, default=False)
    output_format = db.Column(db.Text, default=None)

    # Timelapse
    timelapse_started = db.Column(db.Boolean, default=False)
    timelapse_paused = db.Column(db.Boolean, default=False)
    timelapse_start_time = db.Column(db.Float, default=None)
    timelapse_end_time = db.Column(db.Float, default=None)
    timelapse_interval = db.Column(db.Float, default=None)
    timelapse_next_capture = db.Column(db.Float, default=None)
    timelapse_capture_number = db.Column(db.Integer, default=None)
    timelapse_last_file = db.Column(db.Text, default=None)
    timelapse_last_ts = db.Column(db.Float, default=None)

    # Still tracking
    still_last_file = db.Column(db.Text, default=None)
    still_last_ts = db.Column(db.Float, default=None)

    # Paths
    path_still = db.Column(db.Text, default='')
    path_timelapse = db.Column(db.Text, default='')
    path_video = db.Column(db.Text, default='')

    # Resolutions and stream
    width = db.Column(db.Integer, default=1024)
    height = db.Column(db.Integer, default=768)
    resolution_stream_width = db.Column(db.Integer, default=1024)
    resolution_stream_height = db.Column(db.Integer, default=768)
    stream_fps = db.Column(db.Integer, default=5)

    # picamera options  # TODO: Change to generic variable names next major release
    picamera_shutter_speed = db.Column(db.Integer, default=0)
    picamera_sharpness = db.Column(db.Integer, default=0)
    picamera_iso = db.Column(db.Integer, default=0)
    picamera_awb = db.Column(db.Text, default='auto')
    picamera_awb_gain_red = db.Column(db.Float, default=0.5)
    picamera_awb_gain_blue = db.Column(db.Float, default=0.5)
    picamera_exposure_mode = db.Column(db.Text, default='auto')
    picamera_meter_mode = db.Column(db.Text, default='average')
    picamera_image_effect = db.Column(db.Text, default='none')

    def __repr__(self):
        return "<{cls}(id={s.id}, name='{s.name}', library='{s.library}')>".format(s=self, cls=self.__class__.__name__)
