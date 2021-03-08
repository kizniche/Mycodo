There are several ways to visualize collected data.

## Live Measurements

Page\: `Data -> Live`

The `Live` page is the first page a user sees after logging in to Mycodo. It will display the current measurements being acquired from Input and Function controllers. If there is nothing displayed on the `Live` page, ensure an Input or Function controller is both configured correctly and activated. Data will be automatically updated on the page from the measurement database.

## Asynchronous Graphs

Page\: `Data -> Asynchronous Graphs`

A graphical data display that is useful for viewing data sets spanning relatively long periods of time (weeks/months/years), which could be very data- and processor-intensive to view as a Live Graph. Select a time frame and data will be loaded from that time span, if it exists. The first view will be of the entire selected data set. For every view/zoom, 700 data points will be loaded. If there are more than 700 data points recorded for the time span selected, 700 points will be created from an averaging of the points in that time span. This enables much less data to be used to navigate a large data set. For instance, 4 months of data may be 10 megabytes if all of it were downloaded. However, when viewing a 4 month span, it's not possible to see every data point of that 10 megabytes, and aggregating of points is inevitable. With asynchronous loading of data, you only download what you see. So, instead of downloading 10 megabytes every graph load, only ~50kb will be downloaded until a new zoom level is selected, at which time only another ~50kb is downloaded.

!!! note
    Live Graphs require measurements to be acquired, therefore at least one sensor needs to be added and activated in order to display live data.

## Dashboard

Page\: `Data -> Dashboard`

The dashboard can be used for both viewing data and manipulating the system, thanks to the numerous dashboard widgets available. Widgets are how data is presented to the user and how the user can control aspects of the system from the dashboard. These include graphs, gauges, indicators, and more. For a full list of supported Widgets, see [Supported Widgets](Supported-Widgets.md). Multiple dashboards can be created. Widgets can be moved and arranged on the dashboards by dragging and can be resized by pulling the bottom-left or bottom-right side of the widget.

### Custom Widgets

There is a Custom Widget import system in Mycodo that allows user-created Widgets to be used in the Mycodo system. Custom Widgets can be uploaded on the `[Gear Icon] -> Configure -> Custom Widgets` page. After import, they will be available to use on the `Setup -> Widget` page.

If you develop a working Widget module, please consider [creating a new GitHub issue](https://github.com/kizniche/Mycodo/issues/new?assignees=&labels=&template=feature-request.md&title=New%20Module) or pull request, and it may be included in the built-in set.

Open any of the built-in modules located in the directory [Mycodo/mycodo/widgets](https://github.com/kizniche/Mycodo/tree/master/mycodo/widgets/) for examples of the proper formatting.

There are also example Custom Widgets in the directory [Mycodo/mycodo/widgets/examples](https://github.com/kizniche/Mycodo/tree/master/mycodo/widgets/examples)

Additionally, I have another github repository devoted to Custom Modules that are not included in the built-in set, at [kizniche/Mycodo-custom](https://github.com/kizniche/Mycodo-custom).

### Graph Widget

A graphical data display that is useful for viewing data sets spanning relatively short periods of time (hours/days/weeks). Select a time frame to view data and continually updating data from new sensor measurements. Multiple graphs can be created on one page that enables a dashboard to be created of graphed sensor data. Each graph may have one or more data from inputs, outputs, or PIDs rendered onto it. To edit graph options, select the plus sign on the top-right of a graph.

<table>
<thead>
<tr class="header">
<th>Setting</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td>x-Axis (minutes)</td>
<td>The duration to display on the x-axis of the graph.</td>
</tr>
<tr>
<td>Enable Auto Refresh</td>
<td>Automatically refresh the data on the graph Refresh Period.</td>
</tr>
<tr>
<td>Refresh (seconds)</td>
<td>The duration between acquisitions of new data to display on the graph.</td>
</tr>
<tr>
<td>Inputs/Outputs/PIDs</td>
<td>The Inputs, Outputs, and PIDs to display on the graph.</td>
</tr>
<tr>
<td>Enable X-Axis Reset</td>
<td>Reset the x-axis min/max every time new data comes in during the auto refresh.</td>
</tr>
<tr>
<td>Enable Title</td>
<td>Show a title of the graph name.</td>
</tr>
<tr>
<td>Enable Navbar</td>
<td>Show a slidable navigation bar at the bottom of the graph.</td>
</tr>
<tr>
<td>Enable Export</td>
<td>Enable a button on the top right of the graph to allow exporting of the currently-displayed data as PNG, JPEG, PDF, SVG, CSV, XLS.</td>
</tr>
<tr>
<td>Enable Range Selector</td>
<td>Show a set of navigation buttons at the top of the graph to quickly change the display duration.</td>
</tr>
<tr>
<td>Enable Custom Colors</td>
<td>Use custom colors for Input, Output, and PID lines. Select the colors with the buttons that appear below this checkbox.</td>
</tr>
<tr>
<td>Enable Manual Y-Axis Min/Max</td>
<td>Set the minimum and maximum y-axes of a particular graph. Set both the minimum and maximum to 0 to disable for a particular y-axis.</td>
</tr>
<tr>
<td>Enable Y-Axis Align Ticks</td>
<td>Align the ticks of several y-axes of the same graph.</td>
</tr>
<tr>
<td>Enable Y-Axis Start On Tick</td>
<td>Start all y-axes of a graph on the same tick.</td>
</tr>
<tr>
<td>Enable Y-Axis End On Tick</td>
<td>End all y-axes of a graph on the same tick.</td>
</tr>
</tbody>
</table>

### Gauge Widget

Gauges are visual objects that allow one to quickly see what the latest measurement is of an input. An example that you may be familiar with is a speedometer in a car.

<table>
<thead>
<tr class="header">
<th>Setting</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td>Refresh (seconds)</td>
<td>The duration between acquisitions of new data to display on the graph.</td>
</tr>
<tr>
<td>Max Age (seconds)</td>
<td>The maximum allowable age of the measurement. If the age is greater than this, the gauge will turn off, indicating there is an issue.</td>
</tr>
<tr>
<td>Gauge Min</td>
<td>The lowest value of the gauge.</td>
</tr>
<tr>
<td>Gauge Max</td>
<td>The highest value of the gauge.</td>
</tr>
<tr>
<td>Stops</td>
<td>The number of color ranges on the gauge.</td>
</tr>
<tr>
<td>Show Timestamp</td>
<td>Show the timestamp of the current gauge measurement.</td>
</tr>
</tbody>
</table>

### Camera Widget

Cameras may be added to keep a continuous view on areas.

<table>
<thead>
<tr class="header">
<th>Setting</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td>Refresh (seconds)</td>
<td>The duration between acquisitions of new data to display on the graph.</td>
</tr>
<tr>
<td>Max Age (seconds)</td>
<td>The maximum allowed age of the image timestamp before a &quot;No Recent Image&quot; message is returned.</td>
</tr>
<tr>
<td>Acquire Image (and save new file)</td>
<td>Acquire a new images and save the previous image.</td>
</tr>
<tr>
<td>Acquire Image (and erase last file)</td>
<td>Acquire a new image but erase the previous image.</td>
</tr>
<tr>
<td>Display Live Video Stream</td>
<td>Automatically start a video stream and display it.</td>
</tr>
<tr>
<td>Display Latest Timelapse Image</td>
<td>Display the latest timelapse image that exists.</td>
</tr>
<tr>
<td>Add Timestamp</td>
<td>Append a timestamp to the image.</td>
</tr>
</tbody>
</table>

### Indicator Widget

Shows a green or red button depending if the measurement value is 0 or not 0.

<table>
<thead>
<tr class="header">
<th>Setting</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td>Refresh (seconds)</td>
<td>The duration between acquisitions of new data to display on the graph.</td>
</tr>
<tr>
<td>Max Age (seconds)</td>
<td>The maximum allowable age of the measurement. If the age is greater than this, the gauge will turn off, indicating there is an issue.</td>
</tr>
<tr>
<td>Timestamp Font (em)</td>
<td>The font size of the timestamp value in em.</td>
</tr>
<tr>
<td>Invert</td>
<td>Invert/reverse the colors.</td>
</tr>
<tr>
<td>Measurement</td>
<td>The device to display information about.</td>
</tr>
</tbody>
</table>

### Measurement Widget

<table>
<thead>
<tr class="header">
<th>Setting</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td>Refresh (seconds)</td>
<td>The duration between acquisitions of new data to display on the graph.</td>
</tr>
<tr>
<td>Max Age (seconds)</td>
<td>The maximum allowable age of the measurement. If the age is greater than this, the gauge will turn off, indicating there is an issue.</td>
</tr>
<tr>
<td>Value Font (em)</td>
<td>The font size of the measurement value in em.</td>
</tr>
<tr>
<td>Timestamp Font (em)</td>
<td>The font size of the timestamp value in em.</td>
</tr>
<tr>
<td>Decimal Places</td>
<td>The number of digits to display to the right of the decimal.</td>
</tr>
<tr>
<td>Measurement</td>
<td>The device to display information about.</td>
</tr>
</tbody>
</table>

### Output Widget

<table>
<thead>
<tr class="header">
<th>Setting</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td>Refresh (seconds)</td>
<td>The duration between acquisitions of new data to display on the graph.</td>
</tr>
<tr>
<td>Max Age (seconds)</td>
<td>The maximum allowable age of the measurement. If the age is greater than this, the gauge will turn off, indicating there is an issue.</td>
</tr>
<tr>
<td>Value Font (em)</td>
<td>The font size of the output value in em.</td>
</tr>
<tr>
<td>Timestamp Font (em)</td>
<td>The font size of the timestamp value in em.</td>
</tr>
<tr>
<td>Decimal Places</td>
<td>The number of digits to display to the right of the decimal.</td>
</tr>
<tr>
<td>Feature Output Controls</td>
<td>Display buttons to turn On and Off the relay from the dashboard element.</td>
</tr>
<tr>
<td>Output</td>
<td>The output to display information about.</td>
</tr>
</tbody>
</table>

### Output: PWM Slider Widget

<table>
<thead>
<tr class="header">
<th>Setting</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td>Refresh (seconds)</td>
<td>The duration between acquisitions of new data to display on the graph.</td>
</tr>
<tr>
<td>Max Age (seconds)</td>
<td>The maximum allowable age of the measurement. If the age is greater than this, the gauge will turn off, indicating there is an issue.</td>
</tr>
<tr>
<td>Value Font (em)</td>
<td>The font size of the output value in em.</td>
</tr>
<tr>
<td>Timestamp Font (em)</td>
<td>The font size of the timestamp value in em.</td>
</tr>
<tr>
<td>Decimal Places</td>
<td>The number of digits to display to the right of the decimal.</td>
</tr>
<tr>
<td>Feature Output Controls</td>
<td>Display buttons to turn On and Off the relay from the dashboard element.</td>
</tr>
<tr>
<td>Output</td>
<td>The output to display information about and allow setting the PWM with a slider.</td>
</tr>
</tbody>
</table>

### PID Control Widget

<table>
<thead>
<tr class="header">
<th>Setting</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td>Refresh (seconds)</td>
<td>The duration between acquisitions of new data to display on the graph.</td>
</tr>
<tr>
<td>Max Age (seconds)</td>
<td>The maximum allowable age of the measurement. If the age is greater than this, the gauge will turn off, indicating there is an issue.</td>
</tr>
<tr>
<td>Value Font (em)</td>
<td>The font size of the measurement value in em.</td>
</tr>
<tr>
<td>Timestamp Font (em)</td>
<td>The font size of the timestamp value in em.</td>
</tr>
<tr>
<td>Decimal Places</td>
<td>The number of digits to display to the right of the decimal.</td>
</tr>
<tr>
<td>Show PID Information</td>
<td>Show extra PID information on the dashboard element.</td>
</tr>
<tr>
<td>Show Set Setpoint</td>
<td>Allow setting the PID setpoint on the dashboard element.</td>
</tr>
<tr>
<td>PID</td>
<td>The PID to display information about.</td>
</tr>
</tbody>
</table>

### Python Code Widget

<table>
<thead>
<tr class="header">
<th>Setting</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td>Refresh (seconds)</td>
<td>The duration between acquisitions of new data to display on the graph.</td>
</tr>
<tr>
<td>Value Font (em)</td>
<td>The font size of the text in em.</td>
</tr>
<tr>
<td>Python Code (Loop)</td>
<td>The Python code to execute initially when the controller starts and every Refresh (seconds).</td>
</tr>
<tr>
<td>Python Code (Refresh)</td>
<td>The Python code to execute only when a widget on a dashboard is refreshed, every Refresh (seconds). Note: There may be multiple dashboards calling this function if multiple browser sessions exist.</td>
</tr>
</tbody>
</table>
