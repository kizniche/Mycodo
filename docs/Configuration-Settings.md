Page\: `[Gear Icon] -> Configure`

The settings menu, accessed by selecting the gear icon in the top-right, then the Configure link, is a general area for various system-wide configuration options.

## General Settings

Page\: `[Gear Icon] -> Configure -> General`

<table>
<thead>
<tr class="header">
<th>Setting</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td>Language</td>
<td>Set the language that will be displayed in the web user interface.</td>
</tr>
<tr>
<td>Force HTTPS</td>
<td>Require web browsers to use SSL/HTTPS. Any request to <a href="http://">http://</a> will be redirected to <a href="https://">https://</a>.</td>
</tr>
<tr>
<td>Hide success alerts</td>
<td>Hide all success alert boxes that appear at the top of the page.</td>
</tr>
<tr>
<td>Hide info alerts</td>
<td>Hide all info alert boxes that appear at the top of the page.</td>
</tr>
<tr>
<td>Hide warning alerts</td>
<td>Hide all warning alert boxes that appear at the top of the page.</td>
</tr>
<tr>
<td>Opt-out of statistics</td>
<td>Turn off sending anonymous usage statistics. Please consider that this helps the development to leave on.</td>
</tr>
</tbody>
</table>

## Time Series Database Settings

Page\: `[Gear Icon] -> Configure -> General`

Measurements are stored in a time-series database. There are currently two options that can be used with Mycodo, InfluxDB 1.x and InfluxDB 2.x. InfluxDB 1.x works on both 32-bit and 64-bit operating systems, but 2.x only works on 64-bit operating systems. Therefore, if you are using a 32-bit operating system, you will need to use InfluxDB 1.x. During the Mycodo install, you can select to install influxDB 1.x, 2.x, or neither. If you don't install InfluxDB, you will need to specify the host and credentials to an alternate install for Mycodo to be able to store and query measurements.

If you are installing via Docker, you will need to change the hostname to "mycodo_influxdb" after the Mycodo install to be able to connect to the InfluxDB Docker container.

<table>
<thead>
<tr class="header">
<th>Setting</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td>Database</td>
<td>Select the influxdb version to use.</td>
</tr>
<tr>
<td>Retention Policy</td>
<td>Select the retention policy. Default is "autogen" for v1.x and "infinite" for v2.x.</td>
</tr>
<tr>
<td>Hostname</td>
<td>The hostname to connect to the time-series server. Default is "localhost".</td>
</tr>
<tr>
<td>Port</td>
<td>The time-series database port. Default is 8086.</td>
</tr>
<tr>
<td>Database Name</td>
<td>The name of the database (v1.x) or bucket (v2.x) for Mycodo to store to and query from. Default is "mycodo_db".</td>
</tr>
<tr>
<td>Username</td>
<td>The username to access the database (if credentials are required). Default is "mycodo".</td>
</tr>
<tr>
<td>Password</td>
<td>The password to access the database (if credentials are required).</td>
</tr>
</tbody>
</table>

## Dashboard Settings

Page\: `[Gear Icon] -> Configure -> General`

<table>
<thead>
<tr class="header">
<th>Setting</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td>Grid Cell Height (px)</td>
<td>The height of each widget cell, in pixels.</td>
</tr>
</tbody>
</table>

## Upgrade Settings

Page\: `[Gear Icon] -> Configure -> General`

<table>
<thead>
<tr class="header">
<th>Setting</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td>Internet Test IP Address</td>
<td>The IP address to use to test for an active internet connection.</td>
</tr>
<tr>
<tr>
<td>Internet Test Port</td>
<td>The port to use to test for an active internet connection.</td>
</tr>
<tr>
<tr>
<td>Internet Test Timeout</td>
<td>The timeout period for testing for an active internet connection.</td>
</tr>
<tr>
<td>Check for Updates</td>
<td>Automatically check for updates every 2 days and notify through the web interface. If there is a new update, the Configure (Gear Icon) as well as the Upgrade menu will turn the color red.</td>
</tr>
</tbody>
</table>

## Energy Usage Settings

Page\: `[Gear Icon] -> Configure -> General`

In order to calculate accurate energy usage statistics, a few characteristics of your electrical system needs to be know. These variables should describe the characteristics of the electrical system being used by the relays to operate electrical devices.

!!! note
    If not using a current sensor, proper energy usage calculations will rely on the correct current draw to be set for each output (see [Output Settings](Outputs.md)).

<table>
<thead>
<tr class="header">
<th>Setting</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td>Max Amps</td>
<td>Set the maximum allowed amperage to be switched on at any given time. If a output that's instructed to turn on will cause the sum of active devices to exceed this amount, the output will not be allowed to turn on, to prevent any damage that may result from exceeding current limits.</td>
</tr>
<tr>
<td>Voltage</td>
<td>Alternating current (AC) voltage that is switched by the outputs. This is usually 120 or 240.</td>
</tr>
<tr>
<td>Cost per kWh</td>
<td>This is how much you pay per kWh.</td>
</tr>
<tr>
<td>Currency Unit</td>
<td>This is the unit used for the currency that pays for electricity.</td>
</tr>
<tr>
<td>Day of Month</td>
<td>This is the day of the month (1-30) that the electricity meter is read (which will correspond to the electrical bill).</td>
</tr>
<tr>
<td>Generate Usage/Cost Report</td>
<td>These options define when an Energy Usage Report will be generated. Currently, these Only support the Output Duration calculation method.</td>
</tr>
<tr>
<td>Time Span to Generate</td>
<td>How often to automatically generate a usage/cost report.</td>
</tr>
<tr>
<td>Day of Week/Month to Generate</td>
<td>On which day of the week to generate the report. Daily: 1-7 (Monday = 1), Monthly: 1-28.</td>
</tr>
<tr>
<td>Hour of Day to Generate</td>
<td>On which hour of the day to generate the report (0-23).</td>
</tr>
</tbody>
</table>

## Controller Sample Rate Settings

Page\: `[Gear Icon] -> Configure -> General`

Each controller for Inputs, Outputs, and Functions operate periodically. The fastest these controllers can respond is determined by the sample rate of each. The looping function of each controller is paused for the specific duration. For instance, the Output controller can only have a resolution of 1 second if the sample rate is set to 1 second, meaning if you instruct an output to turn on or off, it will take a maximum of 1 second to respond to that request.

<table>
<thead>
<tr class="header">
<th>Setting</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td>Max Amps</td>
<td>Set the maximum allowed amperage to be switched on at any given time. If a output that's instructed to turn on will cause the sum of active devices to exceed this amount, the output will not be allowed to turn on, to prevent any damage that may result from exceeding current limits.</td>
</tr>
<tr>
<td>Voltage</td>
<td>Alternating current (AC) voltage that is switched by the outputs. This is usually 120 or 240.</td>
</tr>
<tr>
<td>Cost per kWh</td>
<td>This is how much you pay per kWh.</td>
</tr>
<tr>
<td>Currency Unit</td>
<td>This is the unit used for the currency that pays for electricity.</td>
</tr>
<tr>
<td>Day of Month</td>
<td>This is the day of the month (1-30) that the electricity meter is read (which will correspond to the electrical bill).</td>
</tr>
<tr>
<td>Generate Usage/Cost Report</td>
<td>These options define when an Energy Usage Report will be generated. Currently, these Only support the Output Duration calculation method.</td>
</tr>
</tbody>
</table>

## Input Settings

Page\: `[Gear Icon] -> Configure -> Custom Inputs`

Input modules may be imported and used within Mycodo. These modules must follow a specific format. See [Custom Inputs](Inputs.md#custom-inputs) for more details.

<table>
<thead>
<tr class="header">
<th>Setting</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td>Import Input Module</td>
<td>Select your input module file, then click this button to begin the import.</td>
</tr>
</tbody>
</table>

## Output Settings

Page\: `[Gear Icon] -> Configure -> Custom Outputs`

Output modules may be imported and used within Mycodo. These modules must follow a specific format. See [Custom Outputs](Outputs.md#custom-outputs) for more details.

<table>
<thead>
<tr class="header">
<th>Setting</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td>Import Output Module</td>
<td>Select your output module file, then click this button to begin the import.</td>
</tr>
</tbody>
</table>

## Function Settings

Page\: `[Gear Icon] -> Configure -> Custom Functions`

Function modules may be imported and used within Mycodo. These modules must follow a specific format. See [Custom Functions](Functions.md#custom-functions) for more details.

<table>
<thead>
<tr class="header">
<th>Setting</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td>Import Function Module</td>
<td>Select your function module file, then click this button to begin the import.</td>
</tr>
</tbody>
</table>

## Action Settings

Page\: `[Gear Icon] -> Configure -> Custom Actions`

Action modules may be imported and used within Mycodo. These modules must follow a specific format. See [Custom Actions](Actions.md#custom-actions) for more details.

<table>
<thead>
<tr class="header">
<th>Setting</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td>Import Action Module</td>
<td>Select your action module file, then click this button to begin the import.</td>
</tr>
</tbody>
</table>

## Widget Settings

Page\: `[Gear Icon] -> Configure -> Custom Widgets`

Widget modules may be imported and used within Mycodo. These modules must follow a specific format. See [Custom Widgets](Data-Viewing.md#custom-widgets) for more details.

<table>
<thead>
<tr class="header">
<th>Setting</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td>Import Widget Module</td>
<td>Select your widget module file, then click this button to begin the import.</td>
</tr>
</tbody>
</table>

## Measurement Settings

Page\: `[Gear Icon] -> Configure -> Measurements`

New measurements, units, and conversions can be created that can extend functionality of Mycodo beyond the built-in types and equations. Be sure to create units before measurements, as units need to be selected when creating a measurement. A measurement can be created that already exists, allowing additional units to be added to a pre-existing measurement. For example, the measurement 'altitude' already exists, however if you wanted to add the unit 'fathom', first create the unit 'fathom', then create the measurement 'altitude' with the 'fathom' unit selected. It is okay to create a custom measurement for a measurement that already exist (this is how new units for a currently-installed measurement is added).

<table>
<thead>
<tr class="header">
<th>Setting</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td>Measurement ID</td>
<td>ID for the measurement to use in the measurements_dict of input modules (e.g. &quot;length&quot;, &quot;width&quot;, &quot;speed&quot;).</td>
</tr>
<tr>
<td>Measurement Name</td>
<td>Common name for the measurement (e.g. &quot;Length&quot;, &quot;Weight&quot;, &quot;Speed&quot;).</td>
</tr>
<tr>
<td>Measurement Units</td>
<td>Select all the units that are associated with the measurement.</td>
</tr>
<tr>
<td>Unit ID</td>
<td>ID for the unit to use in the measurements_dict of input modules (e.g. &quot;K&quot;, &quot;g&quot;, &quot;m&quot;).</td>
</tr>
<tr>
<td>Unit Name</td>
<td>Common name for the unit (e.g. &quot;Kilogram&quot;, &quot;Meter&quot;).</td>
</tr>
<tr>
<td>Unit Abbreviation</td>
<td>Abbreviation for the unit (e.g. &quot;kg&quot;, &quot;m&quot;).</td>
</tr>
<tr>
<td>Convert From Unit</td>
<td>The unit that will be converted from.</td>
</tr>
<tr>
<td>Convert To Unit</td>
<td>The unit that will be converted to.</td>
</tr>
<tr>
<td>Equation</td>
<td>The equation used to convert one unit to another. The lowercase letter &quot;x&quot; must be included in the equation (e.g. &quot;x/1000+20&quot;, &quot;250*(x/3)&quot;). This &quot;x&quot; will be replaced with the actual measurement being converted.</td>
</tr>
</tbody>
</table>

## User Settings

Page\: `[Gear Icon] -> Configure -> Users`

Mycodo requires at least one Admin user for the login system to be enabled. If there isn't an Admin user, the web server will redirect to an Admin Creation Form. This is the first page you see when starting Mycodo for the first time. After an Admin user has been created, additional users may be created from the User Settings page.

<table>
<thead>
<tr class="header">
<th>Setting</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td>Username</td>
<td>Choose a user name that is between 2 and 64 characters. The user name is case insensitive (all user names are converted to lower-case).</td>
</tr>
<tr>
<td>Email</td>
<td>The email associated with the new account.</td>
</tr>
<tr>
<td>Password/Repeat</td>
<td>Choose a password that is between 6 and 64 characters and only contains letters, numbers, and symbols.</td>
</tr>
<tr>
<td>Keypad Code</td>
<td>Set an optional numeric code that is at least 4 digits for logging in using a keypad.</td>
</tr>
<tr>
<td>Role</td>
<td>Roles are a way of imposing access restrictions on users, to either allow or deny actions. See the table below for explanations of the four default Roles.</td>
</tr>
<tr>
<td>Theme</td>
<td>The web user interface theme to apply, including colors, themes, and other design elements.</td>
</tr>
</tbody>
</table>

### Roles

Roles define the permissions of each user. There are 4 default roles that determine if a user can view or edit particular areas of Mycodo. Four roles are provided by default, but custom roles may be created.

<table>
<thead>
<tr class="header">
<th>Role</th>
<th>Admin</th>
<th>Editor</th>
<th>Monitor</th>
<th>Guest</th>
</tr>
</thead>
<tbody>
<tr>
<td>Edit Users</td>
<td>X</td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>Edit Controllers</td>
<td>X</td>
<td>X</td>
<td></td>
<td></td>
</tr>
<tr>
<td>Edit Settings</td>
<td>X</td>
<td>X</td>
<td></td>
<td></td>
</tr>
<tr>
<td>View Settings</td>
<td>X</td>
<td>X</td>
<td>X</td>
<td></td>
</tr>
<tr>
<td>View Camera</td>
<td>X</td>
<td>X</td>
<td>X</td>
<td></td>
</tr>
<tr>
<td>View Stats</td>
<td>X</td>
<td>X</td>
<td>X</td>
<td></td>
</tr>
<tr>
<td>View Logs</td>
<td>X</td>
<td>X</td>
<td>X</td>
<td></td>
</tr>
</tbody>
</table>

The `Edit Controllers` permission protects the editing of Conditionals, Graphs, LCDs, Methods, PIDs, Outputs, and Inputs.

The `View Stats` permission protects the viewing of usage statistics and the System Information and Energy Usage pages.

## Raspberry Pi Settings

Page\: `[Gear Icon] -> Configure -> Raspberry Pi`

Pi settings configure parts of the linux system that Mycodo runs on.

pigpiod is required if you wish to use PWM Outputs, as well as PWM, RPM, DHT22, DHT11, HTU21D Inputs.

<table>
<thead>
<tr class="header">
<th>Setting</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td>Enable/Disable Feature</td>
<td>These are system interfaces that can be enabled and disabled from the web UI via the <code>raspi-config</code> command.</td>
</tr>
<tr>
<td>pigpiod Sample Rate</td>
<td>This is the sample rate the pigpiod service will operate at. The lower number enables faster PWM frequencies, but may significantly increase processor load on the Pi Zeros. pigpiod may als be disabled completely if it's not required (see note, above).</td>
</tr>
</tbody>
</table>

## Alert Settings

Page\: `[Gear Icon] -> Configure -> Alerts`

Alert settings set up the credentials for sending email notifications.

<table>
<thead>
<tr class="header">
<th>Setting</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td>SMTP Host</td>
<td>The SMTP server to use to send emails from.</td>
</tr>
<tr>
<td>SMTP Port</td>
<td>Port to communicate with the SMTP server (465 for SSL, 587 for TSL).</td>
</tr>
<tr>
<td>Enable SSL</td>
<td>Check to enable SSL, uncheck to enable TSL.</td>
</tr>
<tr>
<td>SMTP User</td>
<td>The user name to send the email from. This can be just a name or the entire email address.</td>
</tr>
<tr>
<td>SMTP Password</td>
<td>The password for the user.</td>
</tr>
<tr>
<td>From Email</td>
<td>What the from email address be set as. This should be the actual email address for this user.</td>
</tr>
<tr>
<td>Max emails (per hour)</td>
<td>Set the maximum number of emails that can be sent per hour. If more notifications are triggered within the hour and this number has been reached, the notifications will be discarded.</td>
</tr>
<tr>
<td>Send Test Email</td>
<td>Test the email configuration by sending a test email.</td>
</tr>
</tbody>
</table>

## Camera Settings

Page\: `[Gear Icon] -> Configure -> Camera`

Many cameras can be used simultaneously with Mycodo. Each camera needs to be set up in the camera settings, then may be used throughout the software.

!!! note
    Not every option (such as Hue or White Balance) may be able to be used with your particular camera, due to manufacturer differences in hardware and software.

<table>
<thead>
<tr class="header">
<th>Setting</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td>Type</td>
<td>Select whether the camera is a Raspberry Pi Camera or a USB camera.</td>
</tr>
<tr>
<td>Library</td>
<td>Select which library to use to communicate with the camera. The Raspberry Pi Camera uses picamera, and USB cameras should be set to fswebcam.</td>
</tr>
<tr>
<td>Device</td>
<td>The device to use to connect to the camera. fswebcam is the only library that uses this option.</td>
</tr>
<tr>
<td>Output</td>
<td>This output will turn on during the capture of any still image (which includes timelapses).</td>
</tr>
<tr>
<td>Output Duration</td>
<td>Turn output on for this duration of time before the image is captured.</td>
</tr>
<tr>
<td>Rotate Image</td>
<td>The number of degrees to rotate the image.</td>
</tr>
<tr>
<td>...</td>
<td>Image Width, Image Height, Brightness, Contrast, Exposure, Gain, Hue, Saturation, White Balance. These options are self-explanatory. Not all options will work with all cameras.</td>
</tr>
<tr>
<td>Pre Command</td>
<td>A command to execute (as user 'root') before a still image is captured.</td>
</tr>
<tr>
<td>Post Command</td>
<td>A command to execute (as user 'root') after a still image is captured.</td>
</tr>
<tr>
<td>Flip horizontally</td>
<td>Flip, or mirror, the image horizontally.</td>
</tr>
<tr>
<td>Flip vertically</td>
<td>Flip, or mirror, the image vertically.</td>
</tr>
</tbody>
</table>

## Diagnostic Settings

Page\: `[Gear Icon] -> Configure -> Diagnostics`

Sometimes issues arise in the system as a result of incompatible configurations, either the result of a misconfigured part of the system (Input, Output, etc.) or an update that didn't properly handle a database upgrade, or other unforeseen issue. Sometimes it is necessary to perform diagnostic actions that can determine the cause of the issue or fix the issue itself. The options below are meant to alleviate issues, such as a misconfigured dashboard element causing an error on the `Data -> Dashboard` page, which may cause an inability to access the `Data -> Dashboard` page to correct the issue. Deleting all Dashboard Elements may be the most economical method to enable access to the `Data -> Dashboard` page again, at the cost of having to readd all the Dashboard Elements that were once there.

<table>
<thead>
<tr class="header">
<th>Setting</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td>Delete All Dashboards</td>
<td>Delete all saved Dashboards on the Data - Dashboard page.</td>
</tr>
<tr>
<td>Delete All Inputs</td>
<td>Delete all Inputs on the Setup -> Input page.</td>
</tr>
<tr>
<td>Delete all Note and Note Tags</td>
<td>Delete all notes and tags from the More -> Note page.</td>
</tr>
<tr>
<td>Delete all Outputs</td>
<td>Delete all Outputs from the Setup -> Output page.</td>
</tr>
<tr>
<td>Delete Settings Database</td>
<td>Delete the mycodo.db settings database (WARNING: This will delete all settings and users).</td>
</tr>
<tr>
<td>Delete File: .dependency</td>
<td>Delete the .dependency file. If you are having an issue accessing the dependency install page, try this.</td>
</tr>
<tr>
<td>Delete File: .upgrade</td>
<td>Delete the .upgrade file. If you are having an issue accessing the upgrade page or running an upgrade, try this.</td>
</tr>
<tr>
<td>Recreate Influxdb 1.x database</td>
<td>Delete the InfluxDB 1.x measurement database, then recreate it. This deletes all measurement data!</td>
</tr>
<tr>
<td>Recreate Influxdb 2.x database</td>
<td>Delete the InfluxDB 2.x measurement database, then recreate it. This deletes all measurement data!</td>
</tr>
<tr>
<td>Reset Email Counter</td>
<td>Reset the email/hour email counter.</td>
</tr>
<tr>
<td>Install Dependencies</td>
<td>Start the dependency install script that will install all needed dependencies for the entire Mycodo system.</td>
</tr>
<tr>
<td>Set to Upgrade to Master</td>
<td>This will change FORCE_UPGRADE_MASTER to True in config.py. This is a way to instruct the upgrade system to upgrade to the master branch on GitHub without having to log in and manually edit the config.py file.</td>
</tr>
</tbody>
</table>
