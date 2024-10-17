# coding=utf-8
from sqlalchemy.dialects.mysql import LONGTEXT

from mycodo.databases import CRUDMixin
from mycodo.databases import set_uuid
from mycodo.mycodo_flask.extensions import db


class Dashboard(CRUDMixin, db.Model):
    __tablename__ = "dashboard"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String(36), nullable=False, unique=True, default=set_uuid)
    name = db.Column(db.Text, nullable=False, unique=True)
    locked = db.Column(db.Boolean, default=False)


class Widget(CRUDMixin, db.Model):
    __tablename__ = "widget"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String(36), nullable=False, unique=True, default=set_uuid)
    graph_type = db.Column(db.Text, default=None)
    dashboard_id = db.Column(db.String(36), default=None)
    name = db.Column(db.Text, default='Widget')
    log_level_debug = db.Column(db.Boolean, default=False)
    font_em_name = db.Column(db.Float, default=1.0)
    enable_drag_handle = db.Column(db.Boolean, default=True)
    position_x = db.Column(db.Integer, default=0)
    position_y = db.Column(db.Integer, default=999)
    width = db.Column(db.Integer, default=6)
    height = db.Column(db.Integer, default=6)
    custom_options = db.Column(db.Text().with_variant(LONGTEXT, "mysql", "mariadb"), default='')

    # TODO: next major revision: delete all below, no longer used
    enable_header_buttons = db.Column(db.Boolean, default=True)
    period = db.Column(db.Float, default=30.0)
    refresh_duration = db.Column(db.Integer, default=120)  # How often to add new data and redraw, refresh camera
    x_axis_duration = db.Column(db.Integer, default=1440)  # X-axis duration (in minutes)
    custom_yaxes = db.Column(db.Text, default='')  # Custom minimum and maximum y-axes
    decimal_places = db.Column(db.Integer, default=1)  # Number of decimal places for displayed value
    enable_status = db.Column(db.Boolean, default=True)
    enable_value = db.Column(db.Boolean, default=True)
    enable_name = db.Column(db.Boolean, default=True)
    enable_unit = db.Column(db.Boolean, default=True)
    enable_measurement = db.Column(db.Boolean, default=True)
    enable_channel = db.Column(db.Boolean, default=True)
    enable_timestamp = db.Column(db.Boolean, default=True)  # Show timestamp for displayed gauge value
    pid_ids = db.Column(db.Text, default='')  # store IDs and measurements to display
    output_ids = db.Column(db.Text, default='')  # store IDs and measurements to display
    math_ids = db.Column(db.Text, default='')  # store Math IDs to display
    note_tag_ids = db.Column(db.Text, default='')  # store Note Tag IDs to display
    input_ids_measurements = db.Column(db.Text, default='')  # store IDs and measurements to display
    enable_navbar = db.Column(db.Boolean, default=False)  # Show navigation bar
    enable_rangeselect = db.Column(db.Boolean, default=False)  # Show range selection buttons
    enable_export = db.Column(db.Boolean, default=False)  # Show export menu
    enable_title = db.Column(db.Boolean, default=False)  # Show title on graph
    enable_auto_refresh = db.Column(db.Boolean, default=True)  # Automatically update graph
    enable_xaxis_reset = db.Column(db.Boolean, default=True)  # Reset the graph x-axis min/max on update
    enable_manual_y_axis = db.Column(db.Boolean, default=False)  # Manual selection of y-axis min/max
    enable_start_on_tick = db.Column(db.Boolean, default=True)  # Enable HighCharts startOnTick
    enable_end_on_tick = db.Column(db.Boolean, default=True)  # Enable HighCharts endOnTick
    enable_align_ticks = db.Column(db.Boolean, default=True)  # Enable HighCharts alignTicks
    use_custom_colors = db.Column(db.Boolean, default=False)  # Enable custom colors of graph series
    custom_colors = db.Column(db.Text, default='')  # Custom hex color values (csv)
    disable_data_grouping = db.Column(db.Text, default='')  # Disable data grouping for measurement IDs
    max_measure_age = db.Column(db.Integer, default=120.0)  # Only show measurements if they are younger than this age
    stops = db.Column(db.Integer, default=None)
    range_colors = db.Column(db.Text, default='')  # Custom hex color values and gauge range
    y_axis_min = db.Column(db.Float, default=None)  # y-axis minimum
    y_axis_max = db.Column(db.Float, default=None)  # y-axis maximum
    option_invert = db.Column(db.Boolean, default=False)
    font_em_value = db.Column(db.Float, default=1.0)  # Font size of value
    font_em_timestamp = db.Column(db.Float, default=1.0)  # Font size of timestamp
    enable_output_controls = db.Column(db.Boolean, default=True)  # Show output controls on dashboard element
    show_pid_info = db.Column(db.Boolean, default=True)  # Display detailed information about the PID
    show_set_setpoint = db.Column(db.Boolean, default=True)  # Display set PID setpoint
    camera_id = db.Column(db.String(36), default='')  # store camera ID to display
    camera_image_type = db.Column(db.Text, default='')  # save new image, overwrite old, display last timelapse
    camera_max_age = db.Column(db.Integer, default=360)  # max camera image age before "No new image" shown

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)
