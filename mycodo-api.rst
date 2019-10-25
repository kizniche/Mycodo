Mycodo API
==========

Daemon Control Object
---------------------

**class mycodo_client.DaemonControl** (*pyro_uri='PYRO:mycodo.pyro_server@127.0.0.1:9090'*, *pyro_timeout=None*)

The mycodo client object implements a way to communicate with a mycodo daemon and query information from the influxdb database.

Parameters

-  **uri** - the pyro5 uri to use to connect to the daemon.
-  **pyro_timeout** - the pyro5 timeout period.

--------------

**controller_activate**(*controller_type*, *controller_id*)

Activates a controller.

Parameters

-  **controller_type** - the type of controller being activated. Options are: "Conditional", "LCD", "Input", "Math", "Output", "PID", "Trigger", or "Custom".
-  **controller_id** - the unique ID of the controller to activate.

--------------

**controller_deactivate**(*controller_type*, *controller_id*)

Deactivates a controller.

Parameters

-  **controller_type** - the type of controller being deactivated. Options are: "Conditional", "LCD", "Input", "Math", "Output", "PID", "Trigger", or "Custom".
-  **controller_id** - the unique ID of the controller to deactivate.

--------------

**get_condition_measurement**(*condition_id*)

Gets the measurement from a Condition of a Conditional Controller.

Parameters

-  **condition_id** - The unique ID of the controller.

--------------

**get_condition_measurement_dict**(*condition_id*)

Gets the measurement dictionary from a Condition of a Conditional Controller.

Parameters

-  **condition_id** - The unique ID of the controller.

--------------

**input_information_get**()

Gets the information about an Input.

--------------

**input_information_update**()

Updates the information about an update from the Input module file.

--------------

**input_force_measurements**(*input_id*)

Induce an Input to conduct a measurement.

Parameters

-  **input_id** - The unique ID of the controller.

--------------

**lcd_backlight**(*lcd_id*, *state*)

Turn the backlight of an LCD on or off, if the LCD supports that functionality.

Parameters

-  **lcd_id** - The unique ID of the controller.
-  **state** - The state of the LCD backlight. Options are: False for off, True for on.

--------------

**lcd_flash**(*lcd_id*, *state*)

Cause the LCD backlight to start or stop flashing, if the LCD supports that functionality.

Parameters

-  **lcd_id** - The unique ID of the controller.
-  **state** - The state of the LCD flashing. Options are: False for off, True for on.

--------------

**lcd_reset**(*lcd_id*)

Reset an LCD to it's default startup state. This can be used to clear the screen, fix display issues, or turn off flashing.

Parameters

-  **lcd_id** - The unique ID of the controller.

--------------

**refresh_daemon_camera_settings**()

Refresh the camera settings stored in the running daemon from the database values.

--------------

**refresh_daemon_conditional_settings**(*unique_id*)

Refresh the Conditional Controller settings of a running Conditional Controller.

Parameters

-  **unique_id** - The unique ID of the controller.

--------------

**refresh_daemon_misc_settings**()

Refresh the miscellaneous settings stored in the running daemon from the database values.

--------------

**refresh_daemon_trigger_settings**(*unique_id*)

Refresh the Trigger Controller settings of a running Trigger Controller.

Parameters

-  **unique_id** - The unique ID of the controller.

--------------

**send_infrared_code_broadcast**(*code*)

Send an infrared command code.

Parameters

-  **code** - The infrared code to send.

--------------

**terminate_daemon**()

Instruct the daemon to shut down.

--------------

**trigger_action**(*action_id*, *message=''*, *single_action=True*, *debug=False*)

Instruct a Function Action to be executed.

Parameters

-  **action_id** - The unique ID of the Function Action.
-  **message** - A message to send with the action that may be used by the action.
-  **single_action** - True if only executing a single action.
-  **debug** - Whether to show debug logging messages.

--------------

**trigger_all_actions**(*function_id*, *message=''*, *debug=False*)

Instruct all Function Actions of a Function Controller to be executed sequentially.

Parameters

-  **function_id** - The unique ID of the controller.
-  **message** - A message to send with the action that may be used by the action.
-  **debug** - Whether to show debug logging messages.

--------------

**output_off**(*output_id*, *trigger_conditionals=True*)

Turn an Output off.

Parameters

-  **output_id** - The unique ID of the Output.
-  **trigger_conditionals** - Whether to trigger controllers that may be monitoring Outputs for state changes.

--------------

**output_on**(*output_id*, *amount=0.0*, *min_off=0.0*, *duty_cycle=0.0*, *trigger_conditionals=True*)

Turn an Output on.

Parameters

-  **output_id** - The unique ID of the Output.
-  **amount** - If on for a duration, this is the float value in seconds.
-  **min_off** - How long to keep the Output off after turning on, if on for a duration.
-  **duty_cycle** - If the Output generates a PWM signal, this is the duty cycle to set, in percent.
-  **trigger_conditionals** - Whether to trigger controllers that may be monitoring Outputs for state changes.

--------------

**output_on_off**(*output_id*, *state*, *amount=0.0*)

Turn an Output on or off.

Parameters

-  **output_id** - The unique ID of the Output.
-  **state** - The state to turn the Output. Options are: "on", "off"
-  **amount** - If turning on for a duration, provide a float value in seconds.

--------------

**output_sec_currently_on**(*output_id*)

Get how many seconds an Output has been on.

Parameters

-  **output_id** - The unique ID of the Output.

--------------

**output_setup**(*action*, *output_id*)

Set up an Output (i.e. load/reload settings from database, initialize any pins/classes, etc.).

Parameters

-  **action** - What action to instruct for the Output. Options are: "Add", "Delete", or "Modify".
-  **output_id** - The unique ID of the Output.

--------------

**output_state**(*output_id*)

Gets the state of an Output. Returns "on" or "off".

Parameters

-  **output_id** - The unique ID of the Output.

--------------

**pid_hold**(*pid_id*)

Set a PID Controller to Hold.

Parameters

-  **pid_id** - The unique ID of the controller.

--------------

**pid_mod**(*pid_id*)

Refresh/Initialize the variables of a running PID controller.

Parameters

-  **pid_id** - The unique ID of the controller.

--------------

**pid_pause**(*pid_id*)

Set a PID Controller to Pause.

Parameters

-  **pid_id** - The unique ID of the controller.

--------------

**pid_resume**(*pid_id*)

Set a PID Controller to Resume.

Parameters

-  **pid_id** - The unique ID of the controller.

--------------

**pid_get**(*pid_id*, *setting*)

Get a parameter of a PID controller.

Parameters

-  **pid_id** - The unique ID of the controller.
-  **setting** - Which option to get. Options are: "setpoint", "error", "integrator", "derivator", "kp", "ki", or "kd".

--------------

**pid_set**(*pid_id*, *setting*, *value*)

Set a parameter of a running PID controller.

Parameters
^^^^^^^^^^

-  **pid_id** - The unique ID of the controller.
-  **setting** - Which option to set. Options are: "setpoint", "method", "integrator", "derivator", "kp", "ki", or "kd".
-  **value** - The value to set.
