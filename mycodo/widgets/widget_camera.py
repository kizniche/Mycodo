# coding=utf-8
#
#  widget_camera.py - Camera dashboard widget
#
#  Copyright (C) 2015-2020 Kyle T. Gabriel <mycodo@kylegabriel.com>
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
#
import logging

from flask_babel import lazy_gettext

logger = logging.getLogger(__name__)


def constraints_pass_positive_value(mod_widget, value):
    """
    Check if the user widget is acceptable
    :param mod_widget: SQL object with user-saved Input options
    :param value: float or int
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure value is positive
    if value <= 0:
        all_passed = False
        errors.append("Must be a positive value")
    return all_passed, errors, mod_widget


WIDGET_INFORMATION = {
    'widget_name_unique': 'widget_camera',
    'widget_name': 'Camera',
    'widget_library': '',
    'no_class': True,

    'message': 'Displays a camera image or stream.',

    'widget_width': 7,
    'widget_height': 8,

    'custom_options': [
        {
            'id': 'camera_id',
            'type': 'select_device',
            'default_value': '',
            'options_select': [
                'Camera',
            ],
            'name': lazy_gettext('Camera'),
            'phrase': lazy_gettext('Select the camera to display')
        },
        {
            'id': 'camera_image_type',
            'type': 'select',
            'default_value': 'new_img',
            'options_select': [
                ('new_img', lazy_gettext('Acquire Image (and save new file)')),
                ('tmp_img', lazy_gettext('Acquire Image (and erase last file)')),
                ('stream', lazy_gettext('Display Live Video Stream')),
                ('timelapse', lazy_gettext('Display Latest Timelapse Image'))
            ],
            'name': lazy_gettext('Image Display Type'),
            'phrase': lazy_gettext('Select how to display the image')
        },
        {
            'id': 'max_age',
            'type': 'integer',
            'default_value': 1200,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Max Age (seconds)',
            'phrase': 'The maximum age of the camera image'
        },
        {
            'id': 'refresh_seconds',
            'type': 'float',
            'default_value': 30.0,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Widget Refresh (seconds)',
            'phrase': 'The period of time between refreshing the widget'
        },
        {
            'id': 'enable_timestamp',
            'type': 'bool',
            'default_value': False,
            'name': lazy_gettext('Show Timestamp'),
            'phrase': lazy_gettext('Show the timestamp on the widget')
        }
    ],

    'widget_dashboard_head': """<!-- No head content -->""",

    'widget_dashboard_title_bar': """<span style="padding-right: 0.5em; font-size: {{each_widget.font_em_name}}em">{% if widget_options['enable_timestamp'] %}<span id="{{each_widget.id}}-timestamp"></span> {% endif %}{{each_widget.name}}</span>""",

    'widget_dashboard_body': """<a id="{{each_widget.id}}-image-href" href="" target="_blank"><img id="{{each_widget.id}}-image-src" style="height: 100%; width: 100%" src=""></a>""",

    'widget_dashboard_js': """<!-- No JS content -->""",

    'widget_dashboard_js_ready': """
  // Capture image and update the image
  function get_image_cam(dashboard_id, camera_unique_id, image_type, max_age) {
    let url = '';
    let image_type_str = '';
    if (image_type === 'tmp_img') {
      url = '/camera_acquire_image/tmp/' + camera_unique_id + '/' + max_age;
      image_type_str = 'still'
    } else if (image_type === 'new_img') {
      url = '/camera_acquire_image/new/' + camera_unique_id + '/' + max_age;
      image_type_str = 'still'
    } else if (image_type === 'timelapse') {
      url = '/camera_latest_timelapse/' + camera_unique_id + '/' + max_age;
      image_type_str = 'timelapse'
    }

    $.ajax(url, {
      success: function(data, responseText, jqXHR) {
        if (jqXHR.status === 204) {
          document.getElementById(dashboard_id + "-image-src").src = "/static/img/image_error.png";
          document.getElementById(dashboard_id + "-image-href").href = "/static/img/image_error.png";
        }
        else {
          let timestamp_str = '';
          if (image_type_str === 'still') timestamp_str = 'Still: ';
          else if (image_type_str === 'timelapse') timestamp_str = 'Timelapse: ';

          const filename = data[0];
          if (filename === 'max_age_exceeded') {
            // The image timestamp is older than the maximum allowable age
            document.getElementById(dashboard_id + "-image-src").src = "/static/img/image_max_age.png";
            document.getElementById(dashboard_id + "-image-href").href = "/static/img/image_max_age.png";
            if (document.getElementById(dashboard_id + "-timestamp")) document.getElementById(dashboard_id + "-timestamp").innerHTML = timestamp_str + "Max Age Exceeded";
          } else if (filename === 'file_not_found') {
            // No image was found in the directory
            document.getElementById(dashboard_id + "-image-src").src = "/static/img/image_error.png";
            document.getElementById(dashboard_id + "-image-href").href = "/static/img/image_error.png";
            if (document.getElementById(dashboard_id + "-timestamp")) document.getElementById(dashboard_id + "-timestamp").innerHTML = timestamp_str + "File Not Found";
          } else {
            // The image is available and younger than the max age
            const timestamp = data[1];
            const image_no_cache_timestamp = Date.now();
            document.getElementById(dashboard_id + "-image-src").src = "/camera/" + camera_unique_id + "/" + image_type_str + "/" + filename + "?" + image_no_cache_timestamp;
            document.getElementById(dashboard_id + "-image-href").href = "/camera/" + camera_unique_id + "/" + image_type_str + "/" + filename + "?" + image_no_cache_timestamp;
            if (document.getElementById(dashboard_id + "-timestamp")) document.getElementById(dashboard_id + "-timestamp").innerHTML = timestamp_str + timestamp;
          }
        }
      },
      error: function(jqXHR, textStatus, errorThrown) {
        document.getElementById(dashboard_id + "-image-src").src = "/static/img/image_error.png";
        document.getElementById(dashboard_id + "-image-href").href = "/static/img/image_error.png";
        if (document.getElementById(dashboard_id + "-timestamp")) document.getElementById(dashboard_id + "-timestamp").innerHTML = "Error Getting Image";
      }
    });
  }
    
  // Repeat function for get_image_cam()
  function repeat_get_image_cam(dashboard_id, camera_unique_id, period_sec, image_type, max_age) {
    if (image_type === 'stream') {
      document.getElementById(dashboard_id + "-image-src").src = "/video_feed/" + camera_unique_id;
      if (document.getElementById(dashboard_id + "-timestamp")) document.getElementById(dashboard_id + "-timestamp").innerHTML = 'Live Stream';
    } else {
      get_image_cam(dashboard_id, camera_unique_id, image_type, max_age);
      setInterval(function () {get_image_cam(dashboard_id, camera_unique_id, image_type, max_age)}, period_sec * 1000);
    }
  }
""",

    'widget_dashboard_js_ready_end': """
$(function() {
  repeat_get_image_cam('{{each_widget.id}}', '{{widget_options['camera_id']}}', {{widget_options['refresh_seconds']}}, '{{widget_options['camera_image_type']}}', {{widget_options['max_age']}});
});
"""
}
