# coding=utf-8
#
#  widget_controller_activate_deactivate.py - Activate/Deactivate Controller
#
#  Copyright (C) 2015-2022 Kyle T. Gabriel <mycodo@kylegabriel.com>
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

from flask import jsonify
from flask_babel import lazy_gettext
from flask_login import current_user

from mycodo.databases.models import Conditional
from mycodo.databases.models import CustomController
from mycodo.databases.models import Function
from mycodo.databases.models import Input
from mycodo.databases.models import Trigger
from mycodo.mycodo_client import DaemonControl
from mycodo.mycodo_flask.utils.utils_general import user_has_permission
from mycodo.utils.constraints_pass import constraints_pass_positive_value

logger = logging.getLogger(__name__)


def controller_state(unique_id):
    if not current_user.is_authenticated:
        return "You are not logged in and cannot access this endpoint"

    input = Input.query.filter(Input.unique_id == unique_id).first()
    function = Function.query.filter(Function.unique_id == unique_id).first()
    customfunction = CustomController.query.filter(CustomController.unique_id == unique_id).first()
    trigger = Trigger.query.filter(Trigger.unique_id == unique_id).first()
    conditional = Conditional.query.filter(Conditional.unique_id == unique_id).first()

    controller = None
    if input:
        controller = input
    elif function:
        controller = function
    elif customfunction:
        controller = customfunction
    elif trigger:
        controller = trigger
    elif conditional:
        controller = conditional

    if controller:
        return jsonify({"status": "Success", "state": controller.is_activated})

    return jsonify({"status": "Error", "state": f"Could not find Controller with ID {unique_id}"})


def controller_activate_deactivate(unique_id, state):
    """Manipulate output (using unique ID)"""
    if not current_user.is_authenticated:
        return "You are not logged in and cannot access this endpoint"
    if not user_has_permission('edit_controllers'):
        return 'Insufficient user permissions to manipulate Controller'

    input = Input.query.filter(Input.unique_id == unique_id).first()
    function = Function.query.filter(Function.unique_id == unique_id).first()
    customfunction = CustomController.query.filter(CustomController.unique_id == unique_id).first()
    trigger = Trigger.query.filter(Trigger.unique_id == unique_id).first()
    conditional = Conditional.query.filter(Conditional.unique_id == unique_id).first()

    controller = None
    if input:
        controller = input
    elif function:
        controller = function
    elif customfunction:
        controller = customfunction
    elif trigger:
        controller = trigger
    elif conditional:
        controller = conditional

    if not controller or not unique_id or state not in ['activate', 'deactivate']:
        return "Invalid inputs: Controller ID or State"

    daemon = DaemonControl()
    if state == 'activate':
        controller.is_activated = True
        controller.save()
        _, return_str = daemon.controller_activate(unique_id)
        return return_str
    elif state == 'deactivate':
        controller.is_activated = False
        controller.save()
        _, return_str = daemon.controller_deactivate(unique_id)
        return return_str

WIDGET_INFORMATION = {
    'widget_name_unique': 'widget_controller_activate_deactivate',
    'widget_name': 'Activate/Deactivate Controller',
    'widget_library': '',
    'no_class': True,

    'message': 'Activate/Deactivate a Controller (Inputs and Functions). For manipulating a PID Controller, use the PID Controller Widget.',

    'widget_width': 4,
    'widget_height': 6,

    'endpoints': [
        # Route URL, route endpoint name, view function, methods
        ("/controller_state/<unique_id>", "controller_state", controller_state, ["GET"]),
        ("/controller_activate_deactivate/<unique_id>/<state>", "controller_activate_deactivate", controller_activate_deactivate, ["GET"])
    ],

    'custom_options': [
        {
            'id': 'controller',
            'type': 'select_device',
            'default_value': '',
            'options_select': [
                'Input',
                'Function',
                'Conditional',
                'Trigger'
            ],
            'name': lazy_gettext('Controller'),
            'phrase': lazy_gettext('Select the Controller to Activate or Deactivate')
        },
        {
            'id': 'refresh_seconds',
            'type': 'float',
            'default_value': 30.0,
            'constraints_pass': constraints_pass_positive_value,
            'name': '{} ({})'.format(lazy_gettext("Refresh"), lazy_gettext("Seconds")),
            'phrase': 'The period of time between refreshing the widget'
        }
    ],

    'widget_dashboard_head': """<!-- No head content -->""",

    'widget_dashboard_title_bar': """
<span id="text-controller-state-{{each_widget.unique_id}}"></span>{{' '}}
<span style="padding-right: 0.5em"> {{each_widget.name}}</span>
""",

    'widget_dashboard_body': """
<div class="pause-background" id="container-controller-{{each_widget.unique_id}}" style="height: 100%">

  <div class="row small-gutters" style="padding: 1em 1.5em 0.5em 1.5em">
    <div id="button-activate-{{each_widget.unique_id}}" class="col-12">
      <input class="btn btn-block btn-primary activate_controller" id="activate_controller" name="{{each_widget.unique_id}}/{{widget_options['controller']}}/activate" type="button" value="{{dict_translation['activate']['title']}}">
    </div>
    <div id="button-deactivate-{{each_widget.unique_id}}" class="col-12">
      <input class="btn btn-block btn-primary deactivate_controller" id="deactivate_controller" name="{{each_widget.unique_id}}/{{widget_options['controller']}}/deactivate" type="button" value="{{dict_translation['deactivate']['title']}}">
    </div>
  </div>

</div>
""",

    'widget_dashboard_js': """
  // Modify Controller
  function adctivate_deactivate_controller(btn_val) {
    const widget_id = btn_val.split('/')[0];
    const controller_id = btn_val.split('/')[1];
    const controller_state = btn_val.split('/')[2];
    $.ajax({
      type: 'GET',
      url: '/controller_activate_deactivate/' + controller_id + '/' + controller_state,
    {% if not misc.hide_alert_success %}
      success: function(data) {
        toastr['success'](data);
        getControllerState(widget_id, controller_id);
      },
    {% endif %}
    {% if not misc.hide_alert_warning %}
      error: function(data) {
        toastr['error'](controller_id + ": " + data);
      }
    {% endif %}
    });
  }

  function print_controller_error(widget_id) {
    document.getElementById('container-controller-' + widget_id).className = "pause-background";
  }

  // Retrieve the controller state
  function getControllerState(widget_id, dev_id) {
    const url = '/controller_state/' + dev_id;
    $.ajax(url, {
      success: function(data, responseText, jqXHR) {
        if (jqXHR.status === 204) {
          print_controller_error(widget_id);
        }
        else {
          if (data['status'] == "Error") {
            print_controller_error(widget_id);
          }
          else if (data['state']) {
            document.getElementById('text-controller-state-' + widget_id).innerHTML = '({{_('Active')}})';
            document.getElementById('container-controller-' + widget_id).className = "active-background";
            document.getElementById('button-activate-' + widget_id).style.display = "none";
            document.getElementById('button-deactivate-' + widget_id).style.display = "block";
          } else {
            document.getElementById('text-controller-state-' + widget_id).innerHTML = '({{_('Inactive')}})';
            document.getElementById('container-controller-' + widget_id).className = "inactive-background";
            document.getElementById('button-activate-' + widget_id).style.display = "block";
            document.getElementById('button-deactivate-' + widget_id).style.display = "none";
          }
        }
      },
      error: function(jqXHR, textStatus, errorThrown) {
        print_controller_error(widget_id);
      }
    });
  }

  // Repeat function for getControllerState()
  function repeatControllerState(widget_id, dev_id, period_sec) {
    setInterval(function () {
      getControllerState(widget_id, dev_id)
    }, period_sec * 1000);
  }
""",

    'widget_dashboard_js_ready': """
  $('.activate_controller').click(function() {
    const btn_val = this.name;
    const id = btn_val.split('/')[0];
    {% if not misc.hide_alert_info %}
    toastr['info']('Command sent to Activate Controller');
    {% endif %}
    adctivate_deactivate_controller(btn_val);
  });
  $('.deactivate_controller').click(function() {
    const btn_val = this.name;
    const id = btn_val.split('/')[0];
    {% if not misc.hide_alert_info %}
    toastr['info']('Command sent to Deactivate Controller');
    {% endif %}
    adctivate_deactivate_controller(btn_val);
  });
""",

    'widget_dashboard_js_ready_end': """
getControllerState('{{each_widget.unique_id}}', '{{widget_options['controller']}}');
repeatControllerState('{{each_widget.unique_id}}', '{{widget_options['controller']}}', {{widget_options['refresh_seconds']}});
"""
}
