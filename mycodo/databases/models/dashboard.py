# coding=utf-8
from mycodo.databases import CRUDMixin
from mycodo.mycodo_flask.extensions import db


class Dashboard(CRUDMixin, db.Model):
    __tablename__ = "graph"  # TODO: rename to 'dashboard'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    graph_type = db.Column(db.Text, default=None)
    name = db.Column(db.Text, default='Graph')
    refresh_duration = db.Column(db.Float, default=120)  # How often to add new data and redraw, refresh camera
    width = db.Column(db.Integer, default=12)  # Width of page (1-12, bootstrap col widths)
    height = db.Column(db.Integer, default=400)  # Height (in pixels)

    # Graph options
    pid_ids = db.Column(db.Text, default='')  # store IDs and measurements to display
    relay_ids = db.Column(db.Text, default='')  # store IDs and measurements to display
    math_ids = db.Column(db.Text, default='')  # store IDs to display
    sensor_ids_measurements = db.Column(db.Text, default='')  # store IDs and measurements to display
    x_axis_duration = db.Column(db.Float, default=1440)  # X-axis duration (in minutes)
    use_custom_colors = db.Column(db.Boolean, default=False)  # Enable custom colors of graph series
    custom_colors = db.Column(db.Text, default='')  # Custom hex color values (csv)
    enable_navbar = db.Column(db.Boolean, default=False)  # Show navigation bar
    enable_rangeselect = db.Column(db.Boolean, default=False)  # Show range selection buttons
    enable_export = db.Column(db.Boolean, default=False)  # Show export menu
    enable_title = db.Column(db.Boolean, default=False)  # Show title on graph
    enable_auto_refresh = db.Column(db.Boolean, default=True)  # Automatically update graph
    enable_xaxis_reset = db.Column(db.Boolean, default=True)  # Reset the graph x-axis min/max on update

    # Gauge options
    y_axis_min = db.Column(db.Float, default=None)  # Gauge minimum
    y_axis_max = db.Column(db.Float, default=None)  # Gauge maximum
    max_measure_age = db.Column(db.Float, default=120.0)  # Only show measurements if they are younger than this age
    range_colors = db.Column(db.Text, default='')  # Custom hex color values and gauge range

    # Camera options
    camera_id = db.Column(db.Text, default='')  # store camera ID to display
    camera_image_type = db.Column(db.Text, default='')  # save new image, overwrite old, display last timelapse
    camera_max_age = db.Column(db.Integer, default=360)  # max camera image age before "No new image" shown

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)
