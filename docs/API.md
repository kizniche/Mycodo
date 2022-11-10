## REST API

As of version 8, Mycodo has a REST API (See [API Endpoint Documentation](https://kizniche.github.io/Mycodo/mycodo-api.html)).

An API is an application programming interface - in short, it’s a set of rules that lets programs talk to each other, exposing data and functionality across the internet in a consistent format.

REST stands for Representational State Transfer. This is an architectural pattern that describes how distributed systems can expose a consistent interface. When people use the term ‘REST API,’ they are generally referring to an API accessed via HTTP protocol at a predefined set of URLs. These URLs represent various resources - any information or content accessed at that location, which can be returned as JSON, HTML, audio files, or images. Often, resources have one or more methods that can be performed on them over HTTP, like GET, POST, PUT and DELETE.

### Authentication

An API Key can be generated from the User Settings page (`[Gear Icon] -> Configure -> Users`). This is stored as a 128-bit bytes object in the database, but will be presented to the user as a base64-encoded string. This can be used to access HTTPS endpoints.

Mycodo supports several authentication methods. All API requests must be made over HTTPS. Calls made over plain HTTP will fail. API requests without authentication will fail.

### Bash Examples

``curl`` can be used, but you must either use ``-k`` to allow the use of an unsigned SSL certificate, or use your own certificate and domain.

```bash
curl -k -v -X GET "https://127.0.0.1/api/settings/users" -H "authorization: Basic 0scjVcxRGi0XczregANBRXG3VMMro+oolPYdauadLblaNThd79bzFPITJjYneU1yK/Ikc9ahHXmll9JiKZO9+hogKoIp2Q8a2cMFBGevgJSd5jYVYz5D83dFE5+OBvvKKaN1U5TvPOXXcj3lkjvPzgxOnEF0CZUsKfU3MA3cFEs=" -H "accept: application/vnd.mycodo.v1+json"
```

```bash
curl -k -v -X GET "https://127.0.0.1/api/settings/users" -H "X-API-KEY: 0scjVcxRGi0XczregANBRXG3VMMro+oolPYdauadLblaNThd79bzFPITJjYneU1yK/Ikc9ahHXmll9JiKZO9+hogKoIp2Q8a2cMFBGevgJSd5jYVYz5D83dFE5+OBvvKKaN1U5TvPOXXcj3lkjvPzgxOnEF0CZUsKfU3MA3cFEs=" -H "accept: application/vnd.mycodo.v1+json"
```

```bash
curl -k -v -X GET "https://127.0.0.1/api/settings/users?api_key=0scjVcxRGi0XczregANBRXG3VMMro+oolPYdauadLblaNThd79bzFPITJjYneU1yK/Ikc9ahHXmll9JiKZO9+hogKoIp2Q8a2cMFBGevgJSd5jYVYz5D83dFE5+OBvvKKaN1U5TvPOXXcj3lkjvPzgxOnEF0CZUsKfU3MA3cFEs=" -H "accept: application/vnd.mycodo.v1+json"
```

### Python Example (GET)

```python
import json
import requests

ip_address = '127.0.0.1'
api_key = 'YOUR_API_KEY'
endpoint = 'settings/inputs'
url = 'https://{ip}/api/{ep}'.format(ip=ip_address, ep=endpoint)
headers = {
    'Accept': 'application/vnd.mycodo.v1+json',
    'X-API-KEY': api_key
}
response = requests.get(url, headers=headers, verify=False)
print("Response Status: {}".format(response.status_code))
print("Response Headers: {}".format(response.headers))
response_dict = json.loads(response.text)
print("Response Dictionary: {}".format(response_dict))
```

### Python Example (POST)

```python
import json
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ip_address = '127.0.0.1'
api_key = 'YOUR_API_KEY'
endpoint = 'outputs/3f5a4806-c830-432d-b329-7821da8336e4'
url = 'https://{ip}/api/{ep}'.format(ip=ip_address, ep=endpoint)
data = {"state": True}  # Turn Output On
headers = {
    'Accept': 'application/vnd.mycodo.v1+json',
    'X-API-KEY': api_key
}
response = requests.post(url, json=data, headers=headers, verify=False)
print("Response Status: {}".format(response.status_code))
print("Response Headers: {}".format(response.headers))
response_dict = json.loads(response.text)
print("Response Dictionary: {}".format(response_dict))
```

### Errors

Mycodo uses conventional HTTP response codes to indicate the success or failure of an API request. In general: Codes in the 2xx range indicate success. Codes in the 4xx range indicate an error that failed given the information provided (e.g., a required parameter was omitted, a charge failed, etc.). Codes in the 5xx range indicate an error with Mycodo's servers (these are rare).

Some 4xx errors that could be handled programmatically (e.g., a card is declined) include an error code that briefly explains the error reported.

### Endpoints

A vendor-specific content type header must be included to determine which API version to use. For version 1, this is "application/vnd.mycodo.v1+json", as can be seen in the examples, above.

Visit https://{RASPBERRY_PI_IP_ADDRESS}/api for documentation of the current API endpoints of your Mycodo install.

Documentation for the latest API version is also available in HTML format: `Mycodo API Docs <https://kizniche.github.io/Mycodo/mycodo-api.html>`__

## Daemon Control Object

### DaemonControl()

**class mycodo_client.DaemonControl**\ (*pyro_uri='PYRO:mycodo.pyro_server@127.0.0.1:9080'*, *pyro_timeout=None*)

The mycodo client object implements a way to communicate with a mycodo daemon and query information from the influxdb database.

Example usage:

```python
from mycodo.mycodo_client import DaemonControl
control = DaemonControl()
control.terminate_daemon()
```

Parameters:

-  **pyro_uri** - the Pyro5 uri to use to connect to the daemon.
-  **pyro_timeout** - the Pyro5 timeout period.

### controller_activate()

**controller_activate**\ (*controller_id*)

Activates a controller.

Parameters:

-  **controller_type** - the type of controller being activated. Options are: "Function", "Input", "Output", "PID", "Trigger", or "Function".
-  **controller_id** - the unique ID of the controller to activate.

### controller_deactivate()

**controller_deactivate**\ (*controller_id*)

Deactivates a controller.

Parameters:

-  **controller_type** - the type of controller being deactivated. Options are: "Conditional", "Input", "Output", "PID", "Trigger", or "Function".
-  **controller_id** - the unique ID of the controller to deactivate.

### get_condition_measurement()

**get_condition_measurement**\ (*condition_id*)

Gets the measurement from a Condition of a Conditional Function.

Parameters:

-  **condition_id** - The unique ID of the controller.

### get_condition_measurement_dict()

**get_condition_measurement_dict**\ (*condition_id*)

Gets the measurement dictionary from a Condition of a Conditional Function.

Parameters:

-  **condition_id** - The unique ID of the controller.

### input_force_measurements()

**input_force_measurements**\ (*input_id*)

Induce an Input to conduct a measurement.

Parameters:

-  **input_id** - The unique ID of the controller.

### lcd_backlight()

**lcd_backlight**\ (*lcd_id*, *state*)

Turn the backlight of an LCD on or off, if the LCD supports that functionality.

Parameters:

-  **lcd_id** - The unique ID of the controller.
-  **state** - The state of the LCD backlight. Options are: False for off, True for on.

### lcd_flash()

**lcd_flash**\ (*lcd_id*, *state*)

Cause the LCD backlight to start or stop flashing, if the LCD supports that functionality.

Parameters:

-  **lcd_id** - The unique ID of the controller.
-  **state** - The state of the LCD flashing. Options are: False for off, True for on.

### lcd_reset()

**lcd_reset**\ (*lcd_id*)

Reset an LCD to its default startup state. This can be used to clear the screen, fix display issues, or turn off flashing.

Parameters:

-  **lcd_id** - The unique ID of the controller.

### output_off()

**output_off**\ (*output_id*, *trigger_conditionals=True*)

Turn an Output off.

Parameters:

-  **output_id** - The unique ID of the Output.
-  **trigger_conditionals** - Whether to trigger controllers that may be monitoring Outputs for state changes.

### output_on()

**output_on**\ (*output_id*, *output_type='sec'*, *amount=0.0*, *min_off=0.0*, *trigger_conditionals=True*)

Turn an Output on.

Parameters:

-  **output_id** - The unique ID of the Output.
-  **output_type** - The type of output to send to the output module (e.g. "sec", "pwm", "vol").
-  **amount** - The amount to send to the output module.
-  **min_off** - How long to keep the Output off after turning on, if on for a duration.
-  **trigger_conditionals** - Whether to trigger controllers that may be monitoring Outputs for state changes.

### output_on_off()

**output_on_off**\ (*output_id*, *state*, *output_type='sec'*, *amount=0.0*,)

Turn an Output on or off.

Parameters:

-  **output_id** - The unique ID of the Output.
-  **state** - The state to turn the Output. Options are: "on", "off"
-  **output_type** - The type of output to send to the output module (e.g. "sec", "pwm", "vol").
-  **amount** - The amount to send to the output module.

### output_sec_currently_on()

**output_sec_currently_on**\ (*output_id*)

Get how many seconds an Output has been on.

Parameters:

-  **output_id** - The unique ID of the Output.

### output_setup()

**output_setup**\ (*action*, *output_id*)

Set up an Output (i.e. load/reload settings from database, initialize any pins/classes, etc.).

Parameters:

-  **action** - What action to instruct for the Output. Options are: "Add", "Delete", or "Modify".
-  **output_id** - The unique ID of the Output.

### output_state()

**output_state**\ (*output_id*)

Gets the state of an Output. Returns "on" or "off" or duty cycle value.

Parameters:

-  **output_id** - The unique ID of the Output.

### pid_get()

**pid_get**\ (*pid_id*, *setting*)

Get a parameter of a PID controller.

Parameters:

-  **pid_id** - The unique ID of the controller.
-  **setting** - Which option to get. Options are: "setpoint", "error", "integrator", "derivator", "kp", "ki", or "kd".

### pid_hold()

**pid_hold**\ (*pid_id*)

Set a PID Controller to Hold.

Parameters:

-  **pid_id** - The unique ID of the controller.

### pid_mod()

**pid_mod**\ (*pid_id*)

Refresh/Initialize the variables of a running PID controller.

Parameters:

-  **pid_id** - The unique ID of the controller.

### pid_pause()

**pid_pause**\ (*pid_id*)

Set a PID Controller to Pause.

Parameters:

-  **pid_id** - The unique ID of the controller.

### pid_resume()

**pid_resume**\ (*pid_id*)

Set a PID Controller to Resume.

Parameters:

-  **pid_id** - The unique ID of the controller.

### pid_set()

**pid_set**\ (*pid_id*, *setting*, *value*)

Set a parameter of a running PID controller.

Parameters:

-  **pid_id** - The unique ID of the controller.
-  **setting** - Which option to set. Options are: "setpoint", "method", "integrator", "derivator", "kp", "ki", or "kd".
-  **value** - The value to set.

### refresh_daemon_conditional_settings()

**refresh_daemon_conditional_settings**\ (*unique_id*)

Refresh the settings of a running Conditional Function.

Parameters:

-  **unique_id** - The unique ID of the controller.

### refresh_daemon_misc_settings()

**refresh_daemon_misc_settings**\ ()

Refresh the miscellaneous settings stored in the running daemon from the database values.

### refresh_daemon_trigger_settings()

**refresh_daemon_trigger_settings**\ (*unique_id*)

Refresh the Trigger Controller settings of a running Trigger Controller.

Parameters:

-  **unique_id** - The unique ID of the controller.

### send_email()

**send_email**\ (*recipients*, *message*, *subject*)

Send an email with the credentials configured for alert notifications.

Parameters:

-  **recipients** - The email address (string) or addresses (list of strings) to send the email.
-  **message** - The body of the email.
-  **subject** - The subject of the email.

### terminate_daemon()

**terminate_daemon**\ ()

Instruct the daemon to shut down.

### trigger_action()

**trigger_action**\ (*action_id*, *message=''*, *single_action=True*, *debug=False*)

Instruct a Function Action to be executed.

Parameters:

-  **action_id** - The unique ID of the Function Action.
-  **message** - A message to send with the action that may be used by the action.
-  **single_action** - True if only executing a single action.
-  **debug** - Whether to show debug logging messages.

### trigger_all_actions()

**trigger_all_actions**\ (*function_id*, *message=''*, *debug=False*)

Instruct all Function Actions of a Function Controller to be executed sequentially.

Parameters:

-  **function_id** - The unique ID of the controller.
-  **message** - A message to send with the action that may be used by the action.
-  **debug** - Whether to show debug logging messages.
