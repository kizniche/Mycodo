# coding=utf-8
from mycodo.databases import CRUDMixin
from mycodo.mycodo_flask.extensions import db


class Graph(CRUDMixin, db.Model):
    __tablename__ = "graph"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    graph_type = db.Column(db.Text, default=None)
    name = db.Column(db.Text, default='Graph')
    pid_ids = db.Column(db.Text, default='')  # store IDs and measurements to display
    relay_ids = db.Column(db.Text, default='')  # store IDs and measurements to display
    math_ids = db.Column(db.Text, default='')  # store IDs to display
    sensor_ids_measurements = db.Column(db.Text, default='')  # store IDs and measurements to display
    width = db.Column(db.Integer, default=100)  # Width of page (in percent)
    height = db.Column(db.Integer, default=400)  # Height (in pixels)
    x_axis_duration = db.Column(db.Float, default=1440)  # X-axis duration (in minutes)
    refresh_duration = db.Column(db.Float, default=120)  # How often to add new data and redraw graph
    use_custom_colors = db.Column(db.Boolean, default=False)  # Enable custom colors of graph series
    custom_colors = db.Column(db.Text, default='')  # Custom hex color values (csv)
    enable_navbar = db.Column(db.Boolean, default=False)  # Show navigation bar
    enable_rangeselect = db.Column(db.Boolean, default=False)  # Show range selection buttons
    enable_export = db.Column(db.Boolean, default=False)  # Show export menu
    enable_title = db.Column(db.Boolean, default=False)  # Show title on graph
    enable_auto_refresh = db.Column(db.Boolean, default=True)  # Automatically update graph
    enable_xaxis_reset = db.Column(db.Boolean, default=True)  # Reset the graph axais min/max on update

    # Gauge options
    y_axis_min = db.Column(db.Float, default=None)  #
    y_axis_max = db.Column(db.Float, default=None)  #
    max_measure_age = db.Column(db.Float, default=120.0)
    range_colors = db.Column(db.Text, default='')  # Custom hex color values and gauge range

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)
