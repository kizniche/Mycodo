## Built-In Actions (System)

### Actions: Pause

- Manufacturer: Mycodo
- Works with: Functions

Set a delay between executing Actions when self.run_all_actions() is used.

Usage: Executing <strong>self.run_action("ACTION_ID")</strong> will create a pause for the set duration. When <strong>self.run_all_actions()</strong> is executed, this will add a pause in the sequential execution of all actions.

#### Options

##### Duration (seconds)

- Type: Decimal
- Description: The duration to pause

### Camera: Capture Photo

- Manufacturer: Mycodo
- Works with: Functions

Capture a photo with the selected Camera.

Usage: Executing <strong>self.run_action("ACTION_ID")</strong> will capture a photo with the selected Camera. Executing <strong>self.run_action("ACTION_ID", value={"camera_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b"})</strong> will capture a photo with the Camera with the specified ID.

#### Options

##### Camera

- Type: Select Device
- Description: Select the Camera to take a photo

### Camera: Time-lapse: Pause

- Manufacturer: Mycodo
- Works with: Functions

Pause a camera time-lapse

Usage: Executing <strong>self.run_action("ACTION_ID")</strong> will pause the selected Camera time-lapse. Executing <strong>self.run_action("ACTION_ID", value={"camera_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b"})</strong> will pause the Camera time-lapse with the specified ID.

#### Options

##### Camera

- Type: Select Device
- Description: Select the Camera to pause the time-lapse

### Camera: Time-lapse: Resume

- Manufacturer: Mycodo
- Works with: Functions

Resume a camera time-lapse

Usage: Executing <strong>self.run_action("ACTION_ID")</strong> will resume the selected Camera time-lapse. Executing <strong>self.run_action("ACTION_ID", value={"camera_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b"})</strong> will resume the Camera time-lapse with the specified ID.

#### Options

##### Camera

- Type: Select Device
- Description: Select the Camera to resume the time-lapse

### Controller: Activate

- Manufacturer: Mycodo
- Works with: Functions

Activate a controller.

Usage: Executing <strong>self.run_action("ACTION_ID")</strong> will activate the selected Controller. Executing <strong>self.run_action("ACTION_ID", value={"controller_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b"})</strong> will activate the controller with the specified ID.

#### Options

##### Controller

- Type: Select Device
- Description: Select the controller to activate

### Controller: Deactivate

- Manufacturer: Mycodo
- Works with: Functions

Deactivate a controller.

Usage: Executing <strong>self.run_action("ACTION_ID")</strong> will deactivate the selected Controller. Executing <strong>self.run_action("ACTION_ID", value={"controller_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b"})</strong> will deactivate the controller with the specified ID.

#### Options

##### Controller

- Type: Select Device
- Description: Select the controller to deactivate

### Create: Note

- Manufacturer: Mycodo
- Works with: Functions

Create a note with the selected Tag.

Usage: Executing <strong>self.run_action("ACTION_ID")</strong> will create a note with the selected tag and note. Executing <strong>self.run_action("ACTION_ID", value={"tags": ["tag1", "tag2"], "name": "My Note", "note": "this is a message"})</strong> will execute the action with the specified list of tag(s) and note. If using only one tag, make it the only element of the list (e.g. ["tag1"]). If note is not specified, then the action message will be used as the note.

#### Options

##### Tags

- Description: Select one or more tags

##### Name

- Type: Text
- Default Value: Name
- Description: The name of the note

##### Note

- Type: Text
- Default Value: Note
- Description: The body of the note

### Execute Command: Shell

- Manufacturer: Mycodo
- Works with: Functions

Execute a Linux bash shell command.

Usage: Executing <strong>self.run_action("ACTION_ID")</strong> will execute the bash command.Executing <strong>self.run_action("ACTION_ID", value={"user": "mycodo", "command": "/home/pi/my_script.sh on"})</strong> will execute the action with the specified command and user.

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
- Works with: Functions

Clear the total volume saved for a flow meter Input. The Input must have the Clear Total Volume option.

Usage: Executing <strong>self.run_action("ACTION_ID")</strong> will clear the total volume for the selected flow meter Input. Executing <strong>self.run_action("ACTION_ID", value={"input_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b"})</strong> will clear the total volume for the flow meter Input with the specified ID.

#### Options

##### Controller

- Type: Select Device
- Description: Select the flow meter Input

### Input: Force Measurements

- Manufacturer: Mycodo
- Works with: Functions

Force measurements to be conducted for an input

Usage: Executing <strong>self.run_action("ACTION_ID")</strong> will force acquiring measurements for the selected Input. Executing <strong>self.run_action("ACTION_ID", value={"input_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b"})</strong> will force acquiring measurements for the Input with the specified ID.

#### Options

##### Input

- Type: Select Device
- Description: Select an Input

### MQTT: Publish

- Manufacturer: Mycodo
- Works with: Functions
- Dependencies: [paho-mqtt](https://pypi.org/project/paho-mqtt)

Publish to an MQTT server.

Usage: Executing <strong>self.run_action("ACTION_ID")</strong> will publish the saved payload text options to the MQTT server. Executing <strong>self.run_action("ACTION_ID", value={"payload": 42})</strong> will publish the specified payload (any type) to the MQTT server. You can also specify the topic (e.g. value={"topic": "my_topic", "payload": 42}). Warning: If using multiple MQTT Inputs or Functions, ensure the Client IDs are unique.

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

##### Payload

- Type: Text
- Description: The payload to publish

##### Keep Alive

- Type: Integer
- Default Value: 60
- Description: The keepalive timeout value for the client. Set to 0 to disable.

##### Client ID

- Type: Text
- Default Value: client_796v1NR4
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
- Description: Password for connecting to the server

### MQTT: Publish: Measurement

- Manufacturer: Mycodo
- Works with: Inputs
- Dependencies: [paho-mqtt](https://pypi.org/project/paho-mqtt)

Publish an Input measurement to an MQTT server.

#### Options

##### Measurement

- Description: Select the measurement to send as the payload

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
- Default Value: client_YeURfmKy
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

### Output: Duty Cycle

- Manufacturer: Mycodo
- Works with: Functions

Set a PWM Output to set a duty cycle.

Usage: Executing <strong>self.run_action("ACTION_ID")</strong> will set the PWM output duty cycle. Executing <strong>self.run_action("ACTION_ID", value={"output_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b", "channel": 0, "duty_cycle": 42})</strong> will set the duty cycle of the PWM output with the specified ID and channel.

#### Options

##### Output

- Type: Select Channel
- Selections: Output_Channels
- Description: Select an output to control

##### Duty Cycle

- Type: Decimal
- Description: Duty cycle for the PWM (percent, 0.0 - 100.0)

### Output: On/Off/Duration

- Manufacturer: Mycodo
- Works with: Functions

Turn an On/Off Output On, Off, or On for a duration.

Usage: Executing <strong>self.run_action("ACTION_ID")</strong> will actuate an output. Executing <strong>self.run_action("ACTION_ID", value={"output_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b", "channel": 0, "state": "on", "duration": 300})</strong> will set the state of the output with the specified ID and channel. If state is on and a duration is set, the output will turn off after the duration.

#### Options

##### Output

- Type: Select Channel
- Selections: Output_Channels
- Description: Select an output to control

##### State

- Type: Select
- Description: Turn the output on or off

##### Duration (seconds)

- Type: Decimal
- Description: If On, you can set a duration to turn the output on. 0 stays on.

### Output: Ramp Duty Cycle

- Manufacturer: Mycodo
- Works with: Functions

Ramp a PWM Output from one duty cycle to another duty cycle over a period of time.

Usage: Executing <strong>self.run_action("ACTION_ID")</strong> will ramp the PWM output duty cycle according to the settings. Executing <strong>self.run_action("ACTION_ID", value={"output_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b", "channel": 0, "start": 42, "end": 62, "increment": 1.0, "duration": 600})</strong> will ramp the duty cycle of the PWM output with the specified ID and channel.

#### Options

##### Output

- Type: Select Channel
- Selections: Output_Channels
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

### Output: Value

- Manufacturer: Mycodo
- Works with: Functions

Send a value to the Output.

Usage: Executing <strong>self.run_action("ACTION_ID")</strong> will actuate a value output. Executing <strong>self.run_action("ACTION_ID", value={"output_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b", "channel": 0, "value": 42})</strong> will send a value to the output with the specified ID and channel.

#### Options

##### Output

- Type: Select Channel
- Selections: Output_Channels
- Description: Select an output to control

##### Value

- Type: Decimal
- Description: The value to send to the output

### Output: Volume

- Manufacturer: Mycodo
- Works with: Functions

Instruct the Output to dispense a volume.

Usage: Executing <strong>self.run_action("ACTION_ID")</strong> will actuate a volume output. Executing <strong>self.run_action("ACTION_ID", value={"output_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b", "channel": 0, "volume": 42})</strong> will send a volume to the output with the specified ID and channel.

#### Options

##### Output

- Type: Select Channel
- Selections: Output_Channels
- Description: Select an output to control

##### Volume

- Type: Decimal
- Description: The volume to send to the output

### PID: Lower: Setpoint

- Manufacturer: Mycodo
- Works with: Functions

Lower the Setpoint of a PID.

Usage: Executing <strong>self.run_action("ACTION_ID")</strong> will lower the setpoint of the selected PID Controller. Executing <strong>self.run_action("ACTION_ID", value={"pid_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b", "amount": 2})</strong> will lower the setpoint of the PID with the specified ID.

#### Options

##### Controller

- Type: Select Device
- Description: Select the PID Controller to lower the setpoint of

##### Lower Setpoint

- Type: Decimal
- Description: The amount to lower the PID setpoint by

### PID: Pause

- Manufacturer: Mycodo
- Works with: Functions

Pause a PID.

Usage: Executing <strong>self.run_action("ACTION_ID")</strong> will pause the selected PID Controller. Executing <strong>self.run_action("ACTION_ID", value="959019d1-c1fa-41fe-a554-7be3366a9c5b")</strong> will pause the PID Controller with the specified ID.

#### Options

##### Controller

- Type: Select Device
- Description: Select the PID Controller to pause

### PID: Raise: Setpoint

- Manufacturer: Mycodo
- Works with: Functions

Raise the Setpoint of a PID.

Usage: Executing <strong>self.run_action("ACTION_ID")</strong> will raise the setpoint of the selected PID Controller. Executing <strong>self.run_action("ACTION_ID", value={"pid_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b", "amount": 2})</strong> will raise the setpoint of the PID with the specified ID.

#### Options

##### Controller

- Type: Select Device
- Description: Select the PID Controller to raise the setpoint of

##### Raise Setpoint

- Type: Decimal
- Description: The amount to raise the PID setpoint by

### PID: Resume

- Manufacturer: Mycodo
- Works with: Functions

Resume a PID.

Usage: Executing <strong>self.run_action("ACTION_ID")</strong> will resume the selected PID Controller. Executing <strong>self.run_action("ACTION_ID", value="959019d1-c1fa-41fe-a554-7be3366a9c5b")</strong> will resume the PID Controller with the specified ID.

#### Options

##### Controller

- Type: Select Device
- Description: Select the PID Controller to resume

### PID: Set Method

- Manufacturer: Mycodo
- Works with: Functions

Select a method to set the PID to use.

Usage: Executing <strong>self.run_action("ACTION_ID")</strong> will pause the selected PID Controller. Executing <strong>self.run_action("ACTION_ID", value={"pid_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b", "method_id": "fe8b8f41-131b-448d-ba7b-00a044d24075"})</strong> will set a method for the PID Controller with the specified IDs.

#### Options

##### Controller

- Type: Select Device
- Description: Select the PID Controller to apply the method

##### Method

- Type: Select Device
- Description: Select the Method to apply to the PID

### PID: Set: Setpoint

- Manufacturer: Mycodo
- Works with: Functions

Set the Setpoint of a PID.

Usage: Executing <strong>self.run_action("ACTION_ID")</strong> will set the setpoint of the selected PID Controller. Executing <strong>self.run_action("ACTION_ID", value={"setpoint": 42})</strong> will set the setpoint of the PID Controller (e.g. 42). You can also specify the PID ID (e.g. value={"setpoint": 42, "pid_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b"})

#### Options

##### Controller

- Type: Select Device
- Description: Select the PID Controller to pause

##### Setpoint

- Type: Decimal
- Description: The setpoint to set the PID Controller

### Send Email

- Manufacturer: Mycodo
- Works with: Functions

Send an email.

Usage: Executing <strong>self.run_action("ACTION_ID")</strong> will email the specified recipient(s) using the SMTP credentials in the system configuration. Separate multiple recipients with commas. The body of the email will be the self-generated message. Executing <strong>self.run_action("ACTION_ID", value={"email_address": ["email1@email.com", "email2@email.com"], "message": "My message"})</strong> will send an email to the specified recipient(s) with the specified message.

#### Options

##### E-Mail Address

- Type: Text
- Default Value: email@domain.com
- Description: E-mail recipient(s) (separate multiple addresses with commas)

### Send Email with Photo

- Manufacturer: Mycodo
- Works with: Functions

Take a photo and send an email with it attached.

Usage: Executing <strong>self.run_action("ACTION_ID")</strong> will take a photo and email it to the specified recipient(s) using the SMTP credentials in the system configuration. Separate multiple recipients with commas. The body of the email will be the self-generated message. Executing <strong>self.run_action("ACTION_ID", value={"camera_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b", "email_address": ["email1@email.com", "email2@email.com"], "message": "My message"})</strong> will capture a photo using the camera with the specified ID and send an email to the specified email(s) with message and attached photo.

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
- Works with: Functions

Restart the System

Usage: Executing <strong>self.run_action("ACTION_ID")</strong> will restart the system in 10 seconds.

### System: Shutdown

- Manufacturer: Mycodo
- Works with: Functions

Shutdown the System

Usage: Executing <strong>self.run_action("ACTION_ID")</strong> will shut down the system in 10 seconds.

### Webhook

- Manufacturer: Mycodo
- Works with: Functions

Emits a HTTP request when triggered. The first line contains a HTTP verb (GET, POST, PUT, ...) followed by a space and the URL to call. Subsequent lines are optional "name: value"-header parameters. After a blank line, the body payload to be sent follows. {{{message}}} is a placeholder that gets replaced by the message, {{{quoted_message}}} is the message in an URL safe encoding.

Usage: Executing <strong>self.run_action("ACTION_ID")</strong> will run the Action.

#### Options

##### Webhook Request

- Description: HTTP request to execute

## Built-In Actions (Devices)

### Display: Backlight: Color

- Manufacturer: Display
- Works with: Functions

Set the display backlight color

Usage: Executing <strong>self.run_action("ACTION_ID")</strong> will change the backlight color on the selected display. Executing <strong>self.run_action("ACTION_ID", value={"display_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b", "color": "255,0,0"})</strong> will change the backlight color on the controller with the specified ID and color.

#### Options

##### Display

- Type: Select Device
- Description: Select the display to set the backlight color

##### Color (RGB)

- Type: Text
- Default Value: 255,0,0
- Description: Color as R,G,B values (e.g. "255,0,0" without quotes)

### Display: Backlight: Off

- Manufacturer: Display
- Works with: Functions

Turn display backlight off

Usage: Executing <strong>self.run_action("ACTION_ID")</strong> will turn the backlight off for the selected display. Executing <strong>self.run_action("ACTION_ID", value={"display_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b"})</strong> will turn the backlight off for the controller with the specified ID.

#### Options

##### Display

- Type: Select Device
- Description: Select the display to turn the backlight off

### Display: Backlight: On

- Manufacturer: Display
- Works with: Functions

Turn display backlight on

Usage: Executing <strong>self.run_action("ACTION_ID")</strong> will turn the backlight on for the selected display. Executing <strong>self.run_action("ACTION_ID", value={"display_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b"})</strong> will turn the backlight on for the controller with the specified ID.

#### Options

##### Display

- Type: Select Device
- Description: Select the display to turn the backlight on

### Display: Flashing: Off

- Manufacturer: Display
- Works with: Functions

Turn display flashing off

Usage: Executing <strong>self.run_action("ACTION_ID")</strong> will stop the backlight flashing on the selected display. Executing <strong>self.run_action("ACTION_ID", value={"display_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b"})</strong> will stop the backlight flashing on the controller with the specified ID.

#### Options

##### Display

- Type: Select Device
- Description: Select the display to stop flashing the backlight

### Display: Flashing: On

- Manufacturer: Display
- Works with: Functions

Turn display flashing on

Usage: Executing <strong>self.run_action("ACTION_ID")</strong> will start the backlight flashing on the selected display. Executing <strong>self.run_action("ACTION_ID", value={"display_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b"})</strong> will start the backlight flashing on the controller with the specified ID.

#### Options

##### Display

- Type: Select Device
- Description: Select the display to start flashing the backlight

