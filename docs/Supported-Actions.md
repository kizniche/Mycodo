Actions allow certain Functions to influence other parts of Mycodo and the computer system.

Supported Actions are listed below.

## Built-In Actions (System)

### Camera: Capture Photo

- Manufacturer: Mycodo

Capture a photo with the selected Camera.

Usage: Executing <strong>self.run_action("{ACTION_ID}")</strong> will capture a photo with the selected Camera. Executing <strong>self.run_action("{ACTION_ID}", value="959019d1-c1fa-41fe-a554-7be3366a9c5b")</strong> will capture a photo with the Camera with the specified ID (e.g. 959019d1-c1fa-41fe-a554-7be3366a9c5b).

#### Options

##### Camera

- Type: Select Device
- Description: Select the Camera to take a photo with

### Camera: Time-lapse: Pause

- Manufacturer: Mycodo

Pause a camera time-lapse

Usage: Executing <strong>self.run_action("{ACTION_ID}")</strong> will pause the selected Camera time-lapse. Executing <strong>self.run_action("{ACTION_ID}", value="959019d1-c1fa-41fe-a554-7be3366a9c5b")</strong> will pause the Camera time-lapse with the specified ID (e.g. 959019d1-c1fa-41fe-a554-7be3366a9c5b).

#### Options

##### Camera

- Type: Select Device
- Description: Select the Camera to pause the time-lapse

### Camera: Time-lapse: Resume

- Manufacturer: Mycodo

Resume a camera time-lapse

Usage: Executing <strong>self.run_action("{ACTION_ID}")</strong> will resume the selected Camera time-lapse. Executing <strong>self.run_action("{ACTION_ID}", value="959019d1-c1fa-41fe-a554-7be3366a9c5b")</strong> will resume the Camera time-lapse with the specified ID (e.g. 959019d1-c1fa-41fe-a554-7be3366a9c5b).

#### Options

##### Camera

- Type: Select Device
- Description: Select the Camera to resume the time-lapse

### Controller: Activate

- Manufacturer: Mycodo

Activate a controller.

Usage: Executing <strong>self.run_action("{ACTION_ID}")</strong> will activate the selected Controller. Executing <strong>self.run_action("{ACTION_ID}", value={"controller_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b"})</strong> will activate the controller with the specified ID (e.g. 959019d1-c1fa-41fe-a554-7be3366a9c5b).

#### Options

##### Controller

- Type: Select Device
- Description: Select the controller to activate

### Controller: Deactivate

- Manufacturer: Mycodo

Deactivate a controller.

Usage: Executing <strong>self.run_action("{ACTION_ID}")</strong> will deactivate the selected Controller. Executing <strong>self.run_action("{ACTION_ID}", value={"controller_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b"})</strong> will deactivate the controller with the specified ID (e.g. 959019d1-c1fa-41fe-a554-7be3366a9c5b).

#### Options

##### Controller

- Type: Select Device
- Description: Select the controller to deactivate

### Create: Note

- Manufacturer: Mycodo

Create a note with the selected Tag.

Usage: Executing <strong>self.run_action("{ACTION_ID}")</strong> will create a note with the selected tag and note. Executing <strong>self.run_action("{ACTION_ID}", value=["tag1,tag2", "note"])</strong> will create a note with the tag(s) (multiple separated by commas) and note (e.g. tags "tag1,tag2" and note "note"). If note is not specified, then the action message is saved as the note (e.g. value=["tag1", ""])

#### Options

##### Note Tags

- Description: Select one or more tags

##### Note

- Type: Text
- Description: The body of the note

### Execute Command: Shell

- Manufacturer: Mycodo

Execute a Linux bash shell command.

Usage: Executing <strong>self.run_action("{ACTION_ID}")</strong> will execute the bash command.

#### Options

##### User

- Type: Text
- Default Value: mycodo
- Description: The user to execute the command

##### Command

- Type: Text
- Default Value: /home/pi/my_script.sh on
- Description: Command to execute

### Flow Meter: Clear Total Volume

- Manufacturer: Mycodo

Clear the total volume saved for a flow meter Input. The Input must have the Clear Total Volume option.

Usage: Executing <strong>self.run_action("{ACTION_ID}")</strong> will clear the total volume for the selected flow meter Input. Executing <strong>self.run_action("{ACTION_ID}", value="959019d1-c1fa-41fe-a554-7be3366a9c5b")</strong> will clear the total volume for the flow meter Input with the specified ID (e.g. 959019d1-c1fa-41fe-a554-7be3366a9c5b).

#### Options

##### Controller

- Type: Select Device
- Description: Select the flow meter Input

### Input: Force Measurements

- Manufacturer: Mycodo

Force measurements to be conducted for an input

Usage: Executing <strong>self.run_action("{ACTION_ID}")</strong> will force acquiring measurements for the selected Input. Executing <strong>self.run_action("{ACTION_ID}", value={"input_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b"})</strong> will force acquiring measurements for the Input with the specified ID (e.g. 959019d1-c1fa-41fe-a554-7be3366a9c5b),

#### Options

##### Input

- Type: Select Device
- Description: Select an Input

### MQTT: Publish

- Manufacturer: Mycodo
- Dependencies: [paho-mqtt](https://pypi.org/project/paho-mqtt)

Publish to an MQTT server.

Usage: Executing <strong>self.run_action("{ACTION_ID}", value={"payload": 42})</strong> will publish a value (e.g. 42) to the specified MQTT server. You can also specify the topic with the key "topic" (e.g. value={"topic": "my_topic", "payload": 42}). Warning: If using multiple MQTT Inputs or Functions, ensure the Client IDs are unique.

#### Options

##### Hostname

- Type: Text
- Default Value: localhost
- Description: The hostname of the MQTT server

##### Port

- Type: Integer
- Default Value: 1883
- Description: The port of the MQTT server

##### Topic

- Type: Text
- Default Value: paho/test/single
- Description: The topic to publish with

##### Keep Alive

- Type: Integer
- Default Value: 60
- Description: The keepalive timeout value for the client. Set to 0 to disable.

##### Client ID

- Type: Text
- Default Value: client_JGenHhc0
- Description: Unique client ID for connecting to the MQTT server

##### Use Login

- Type: Boolean
- Description: Send login credentials

##### Username

- Type: Text
- Default Value: user
- Description: Username for connecting to the server

##### Password

- Type: Text
- Description: Password for connecting to the server.

### Output (Duty Cycle)

- Manufacturer: Mycodo

Set a PWM Output to set a duty cycle.

Usage: Executing <strong>self.run_action("{ACTION_ID}")</strong> will set the PWM output duty cycle. Executing <strong>self.run_action("{ACTION_ID}", value=42)</strong> will set the PWM output duty cycle to a specific value (e.g. 42%).

#### Options

##### Output

- Type: Select Device, Measurement, and Channel
- Selections: Output
- Description: Select an output to control

##### Duty Cycle

- Type: Decimal
- Description: Duty cycle for the PWM (percent, 0.0 - 100.0)

### Output (On/Off/Duration)

- Manufacturer: Mycodo

Turn an On/Off Output On, Off, or On for a duration.

Usage: Executing <strong>self.run_action("{ACTION_ID}")</strong> will actuate an output. Executing <strong>self.run_action("{ACTION_ID}", value=["on", 300])</strong> will set the output state to the values sent (e.g. on for 300 seconds).

#### Options

##### Output

- Type: Select Device, Measurement, and Channel
- Selections: Output
- Description: Select an output to control

##### Output State

- Type: Select
- Description: Turn the output on or off

##### Duration (seconds)

- Type: Decimal
- Description: If On, you can set a duration to turn the output on. 0 stays on.

### Output (Ramp Duty Cycle)

- Manufacturer: Mycodo

Ramp a PWM Output from one duty cycle to another duty cycle over a period of time.

Usage: Executing <strong>self.run_action("{ACTION_ID}")</strong> will ramp the PWM output duty cycle according to the settings. Executing <strong>self.run_action("{ACTION_ID}", value=[42, 62, 1.0, 600])</strong> will ramp the PWM output duty cycle to the values sent (e.g. 42% to 62% at increments of 1.0 % 0ver 600 seconds).

#### Options

##### Output

- Type: Select Device, Measurement, and Channel
- Selections: Output
- Description: Select an output to control

##### Duty Cycle: Start

- Type: Decimal
- Description: Duty cycle for the PWM (percent, 0.0 - 100.0)

##### Duty Cycle: End

- Type: Decimal
- Default Value: 50.0
- Description: Duty cycle for the PWM (percent, 0.0 - 100.0)

##### Increment (Duty Cycle)

- Type: Decimal
- Default Value: 1.0
- Description: How much to change the duty cycle every Duration

##### Duration (seconds)

- Type: Decimal
- Description: How long to ramp from start to finish.

### Output (Value)

- Manufacturer: Mycodo

Send a value to the Output.

Usage: Executing <strong>self.run_action("{ACTION_ID}")</strong> will actuate a value output. Executing <strong>self.run_action("{ACTION_ID}", value=42)</strong> will actuate a value output with a specific value (e.g. 42).

#### Options

##### Output

- Type: Select Device, Measurement, and Channel
- Selections: Output
- Description: Select an output to control

##### Duty Cycle

- Type: Decimal
- Description: Duty cycle for the PWM (percent, 0.0 - 100.0)

### Output (Volume)

- Manufacturer: Mycodo

Instruct the Output to dispense a volume.

Usage: Executing <strong>self.run_action("{ACTION_ID}")</strong> will actuate a volume output. Executing <strong>self.run_action("{ACTION_ID}", value=42)</strong> will actuate a volume output with a specific volume (e.g. 42 ml).

#### Options

##### Output

- Type: Select Device, Measurement, and Channel
- Selections: Output
- Description: Select an output to control

##### Duty Cycle

- Type: Decimal
- Description: Duty cycle for the PWM (percent, 0.0 - 100.0)

### PID: Lower: Setpoint

- Manufacturer: Mycodo

Lower the Setpoint of a PID.

Usage: Executing <strong>self.run_action("{ACTION_ID}")</strong> will lower the setpoint of the selected PID Controller. Executing <strong>self.run_action("{ACTION_ID}", value={"amount": 2})</strong> will lower the setpoint of the PID Controller (e.g. 2). You can also specify the PID ID (e.g. value={"amount": 2, "pid_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b"})

#### Options

##### Controller

- Type: Select Device
- Description: Select the PID Controller to lower the setpoint of

##### Lower Setpoint

- Type: Decimal
- Description: The amount to lower the PID setpoint by

### PID: Pause

- Manufacturer: Mycodo

Pause a PID.

Usage: Executing <strong>self.run_action("{ACTION_ID}")</strong> will pause the selected PID Controller. Executing <strong>self.run_action("{ACTION_ID}", value="959019d1-c1fa-41fe-a554-7be3366a9c5b")</strong> will pause the PID Controller with the specified ID (e.g. 959019d1-c1fa-41fe-a554-7be3366a9c5b).

#### Options

##### Controller

- Type: Select Device
- Description: Select the PID Controller to pause

### PID: Raise: Setpoint

- Manufacturer: Mycodo

Raise the Setpoint of a PID.

Usage: Executing <strong>self.run_action("{ACTION_ID}")</strong> will raise the setpoint of the selected PID Controller. Executing <strong>self.run_action("{ACTION_ID}", value={"amount": 2})</strong> will raise the setpoint of the PID Controller (e.g. 2). You can also specify the PID ID (e.g. value={"amount": 2, "pid_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b"})

#### Options

##### Controller

- Type: Select Device
- Description: Select the PID Controller to raise the setpoint of

##### Raise Setpoint

- Type: Decimal
- Description: The amount to raise the PID setpoint by

### PID: Resume

- Manufacturer: Mycodo

Resume a PID.

Usage: Executing <strong>self.run_action("{ACTION_ID}")</strong> will resume the selected PID Controller. Executing <strong>self.run_action("{ACTION_ID}", value="959019d1-c1fa-41fe-a554-7be3366a9c5b")</strong> will resume the PID Controller with the specified ID (e.g. 959019d1-c1fa-41fe-a554-7be3366a9c5b).

#### Options

##### Controller

- Type: Select Device
- Description: Select the PID Controller to resume

### PID: Set Method

- Manufacturer: Mycodo

Select a method to set the PID to use.

Usage: Executing <strong>self.run_action("{ACTION_ID}")</strong> will pause the selected PID Controller. Executing <strong>self.run_action("{ACTION_ID}", value={"pid_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b", "method_id": "fe8b8f41-131b-448d-ba7b-00a044d24075"})</strong> will set the PID Controller with the specified ID (e.g. 959019d1-c1fa-41fe-a554-7be3366a9c5b) to the method with the specified ID (e.g. "fe8b8f41-131b-448d-ba7b-00a044d24075").

#### Options

##### Controller

- Type: Select Device
- Description: Select the PID Controller to apply the method

##### Method

- Type: Select Device
- Description: Select the Method to apply to the PID

### PID: Set: Setpoint

- Manufacturer: Mycodo

Set the Setpoint of a PID.

Usage: Executing <strong>self.run_action("{ACTION_ID}")</strong> will set the setpoint of the selected PID Controller. Executing <strong>self.run_action("{ACTION_ID}", value={"setpoint": 42})</strong> will set the setpoint of the PID Controller (e.g. 42). You can also specify the PID ID (e.g. value={"setpoint": 42, "pid_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b"})

#### Options

##### Controller

- Type: Select Device
- Description: Select the PID Controller to pause

##### Setpoint

- Type: Decimal
- Description: The setpoint to set the PID Controller

### Pause

- Manufacturer: Mycodo

Set a delay between executing Actions when self.run_all_actions() is used.

Usage: Executing <strong>self.run_action("{ACTION_ID}")</strong> will create a pause for the set duration. When <strong>self.run_all_actions()</strong> is executed, this will add a pause in the sequential execution of all actions.

#### Options

##### Duration (seconds)

- Type: Decimal
- Description: The duration to pause

### Send Email

- Manufacturer: Mycodo

Send an email.

Usage: Executing <strong>self.run_action("{ACTION_ID}")</strong> will email the specified recipient(s) using the SMTP credentials in the system configuration. Separate multiple recipients with commas. The body of the email will be the self-generated message. Executing <strong>self.run_action("{ACTION_ID}", value="Email message here")</strong> will send an email with the specified message.

#### Options

##### E-Mail Address

- Type: Text
- Default Value: email@domain.com
- Description: E-mail recipient(s). Separate multiple with commas.

### Send Email with Photo

- Manufacturer: Mycodo

Take a photo and send an email with it attached.

Usage: Executing <strong>self.run_action("{ACTION_ID}")</strong> will take a photo and email it to the specified recipient(s) using the SMTP credentials in the system configuration. Separate multiple recipients with commas. The body of the email will be the self-generated message. Executing <strong>self.run_action("{ACTION_ID}", value={"message": "Email message here"})</strong> will send an email with the specified message. A Camera ID can also be specified (e.g. value={"camera_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b", "message": "Email message here"}).

#### Options

##### Camera

- Type: Select Device
- Description: Select the Camera to take a photo with

##### E-Mail Address

- Type: Text
- Default Value: email@domain.com
- Description: E-mail recipient(s). Separate multiple with commas.

### System: Restart

- Manufacturer: Mycodo

Restart the System

Usage: Executing <strong>self.run_action("{ACTION_ID}")</strong> will restart the system in 10 seconds.

### System: Shutdown

- Manufacturer: Mycodo

Shutdown the System

Usage: Executing <strong>self.run_action("{ACTION_ID}")</strong> will shut down the system in 10 seconds.

### Webhook

- Manufacturer: Mycodo

Emits a HTTP request when triggered. The first line contains a HTTP verb (GET, POST, PUT, ...) followed by a space and the URL to call. Subsequent lines are optional "name: value"-header parameters. After a blank line, the body payload to be sent follows. {{{message}}} is a placeholder that gets replaced by the message, {{{quoted_message}}} is the message in an URL safe encoding.

Usage: Executing <strong>self.run_action("{ACTION_ID}")</strong> will run the Action.

#### Options

##### Webhook Request

- Description: HTTP request to execute

## Built-In Actions (Devices)

### Display: Backlight: Color

- Manufacturer: Disaplay

Set the display backlight color

Usage: Executing <strong>self.run_action("{ACTION_ID}")</strong> will change the backlight color on the selected display. Executing <strong>self.run_action("{ACTION_ID}", value={"display_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b", "color": "255,0,0"})</strong> will change the backlight color on the controller with the specified ID and color (e.g. 959019d1-c1fa-41fe-a554-7be3366a9c5b and 255,0,0).

#### Options

##### Display

- Type: Select Device
- Description: Select the display to set the backlight color

##### Color (RGB)

- Type: Text
- Default Value: 255,0,0
- Description: Color as R,G,B values (e.g. "255,0,0" without quotes)

### Display: Backlight: Off

- Manufacturer: Disaplay

Turn display backlight off

Usage: Executing <strong>self.run_action("{ACTION_ID}")</strong> will turn the backlight off for the selected display. Executing <strong>self.run_action("{ACTION_ID}", value={"display_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b"})</strong> will turn the backlight off for the controller with the specified ID (e.g. 959019d1-c1fa-41fe-a554-7be3366a9c5b).

#### Options

##### Display

- Type: Select Device
- Description: Select the display to turn the backlight off

### Display: Backlight: On

- Manufacturer: Disaplay

Turn display backlight on

Usage: Executing <strong>self.run_action("{ACTION_ID}")</strong> will turn the backlight on for the selected display. Executing <strong>self.run_action("{ACTION_ID}", value={"display_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b"})</strong> will turn the backlight on for the controller with the specified ID (e.g. 959019d1-c1fa-41fe-a554-7be3366a9c5b).

#### Options

##### Display

- Type: Select Device
- Description: Select the display to turn the backlight on

### Display: Flashing: Off

- Manufacturer: Disaplay

Turn display flashing off

Usage: Executing <strong>self.run_action("{ACTION_ID}")</strong> will stop the backlight flashing on the selected display. Executing <strong>self.run_action("{ACTION_ID}", value={"display_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b"})</strong> will stop the backlight flashing on the controller with the specified ID (e.g. 959019d1-c1fa-41fe-a554-7be3366a9c5b).

#### Options

##### Display

- Type: Select Device
- Description: Select the display to stop flashing the backlight

### Display: Flashing: On

- Manufacturer: Disaplay

Turn display flashing on

Usage: Executing <strong>self.run_action("{ACTION_ID}")</strong> will start the backlight flashing on the selected display. Executing <strong>self.run_action("{ACTION_ID}", value={"display_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b"})</strong> will start the backlight flashing on the controller with the specified ID (e.g. 959019d1-c1fa-41fe-a554-7be3366a9c5b).

#### Options

##### Display

- Type: Select Device
- Description: Select the display to start flashing the backlight

