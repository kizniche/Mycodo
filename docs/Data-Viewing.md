There are several ways to visualize collected data. Additionally, the dashboard can be used for both viewing data and manipulating the system, thanks to the numerous dashboard widgets available.

## Live Measurements

`Data -> Live`

The `Live` page is the first page a user sees after logging in to Mycodo. It will display the current measurements being acquired from Input and Math controllers. If there is nothing displayed on the `Live` page, ensure an Input or Math controller is both configured correctly and activated. Data will be automatically updated on the page from the measurement database.

## Asynchronous Graphs

`Data -> Asynchronous Graphs`

A graphical data display that is useful for viewing data sets spanning relatively long periods of time (weeks/months/years), which could be very data- and processor-intensive to view as a Live Graph. Select a time frame and data will be loaded from that time span, if it exists. The first view will be of the entire selected data set. For every view/zoom, 700 data points will be loaded. If there are more than 700 data points recorded for the time span selected, 700 points will be created from an averaging of the points in that time span. This enables much less data to be used to navigate a large data set. For instance, 4 months of data may be 10 megabytes if all of it were downloaded. However, when viewing a 4 month span, it's not possible to see every data point of that 10 megabytes, and aggregating of points is inevitable. With asynchronous loading of data, you only download what you see. So, instead of downloading 10 megabytes every graph load, only ~50kb will be downloaded until a new zoom level is selected, at which time only another ~50kb is downloaded.

!!! note
    Live Graphs require measurements to be acquired, therefore at least one sensor needs to be added and activated in order to display live data.

## Dashboard

`Data -> Dashboard`

Dashboards are where you can add widgets to display data and interact with the system. Multiple dashboards can be created. Widgets can be moved and arranged on the dashboards by dragging the top header and can be resized by dragging the bottom-left or bottom-right side of the widget. Specific options for widgets are below.

### Graph Widget

A graphical data display that is useful for viewing data sets spanning relatively short periods of time (hours/days/weeks). Select a time frame to view data and continually updating data from new sensor measurements. Multiple graphs can be created on one page that enables a dashboard to be created of graphed sensor data. Each graph may have one or more data from inputs, outputs, or PIDs rendered onto it. To edit graph options, select the plus sign on the top-right of a graph.

<table>
<col width="40%" />
<col width="59%" />
<thead>
<tr class="header">
<th align="left">Setting</th>
<th align="left">Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td align="left">x-Axis (minutes)</td>
<td align="left">The duration to display on the x-axis of the graph.</td>
</tr>
<tr class="even">
<td align="left">Enable Auto Refresh</td>
<td align="left">Automatically refresh the data on the graph Refresh Period.</td>
</tr>
<tr class="odd">
<td align="left">Refresh (seconds)</td>
<td align="left">The duration between acquisitions of new data to display on the graph.</td>
</tr>
<tr class="even">
<td align="left">Inputs/Outputs/PIDs</td>
<td align="left">The Inputs, Outputs, and PIDs to display on the graph.</td>
</tr>
<tr class="odd">
<td align="left">Enable X-Axis Reset</td>
<td align="left">Reset the x-axis min/max every time new data comes in during the auto refresh.</td>
</tr>
<tr class="even">
<td align="left">Enable Title</td>
<td align="left">Show a title of the graph name.</td>
</tr>
<tr class="odd">
<td align="left">Enable Navbar</td>
<td align="left">Show a slidable navigation bar at the bottom of the graph.</td>
</tr>
<tr class="even">
<td align="left">Enable Export</td>
<td align="left">Enable a button on the top right of the graph to allow exporting of the currently-displayed data as PNG, JPEG, PDF, SVG, CSV, XLS.</td>
</tr>
<tr class="odd">
<td align="left">Enable Range Selector</td>
<td align="left">Show a set of navigation buttons at the top of the graph to quickly change the display duration.</td>
</tr>
<tr class="even">
<td align="left">Enable Graph Shift</td>
<td align="left">If enabled, old data points are removed when new data is added to the graph. Only recommended to enable if Enable Navbar is enabled.</td>
</tr>
<tr class="odd">
<td align="left">Enable Custom Colors</td>
<td align="left">Use custom colors for Input, Output, and PID lines. Select the colors with the buttons that appear below this checkbox.</td>
</tr>
<tr class="even">
<td align="left">Enable Manual Y-Axis Min/Max</td>
<td align="left">Set the minimum and maximum y-axes of a particular graph. Set both the minimum and maximum to 0 to disable for a particular y-axis.</td>
</tr>
<tr class="odd">
<td align="left">Enable Y-Axis Align Ticks</td>
<td align="left">Align the ticks of several y-axes of the same graph.</td>
</tr>
<tr class="even">
<td align="left">Enable Y-Axis Start On Tick</td>
<td align="left">Start all y-axes of a graph on the same tick.</td>
</tr>
<tr class="odd">
<td align="left">Enable Y-Axis End On Tick</td>
<td align="left">End all y-axes of a graph on the same tick.</td>
</tr>
</tbody>
</table>

### Gauge Widget

Gauges are visual objects that allow one to quickly see what the latest measurement is of an input. An example that you may be familiar with is a speedometer in a car.

<table>
<col width="40%" />
<col width="59%" />
<thead>
<tr class="header">
<th align="left">Setting</th>
<th align="left">Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td align="left">Refresh (seconds)</td>
<td align="left">The duration between acquisitions of new data to display on the graph.</td>
</tr>
<tr class="even">
<td align="left">Max Age (seconds)</td>
<td align="left">The maximum allowable age of the measurement. If the age is greater than this, the gauge will turn off, indicating there is an issue.</td>
</tr>
<tr class="odd">
<td align="left">Gauge Min</td>
<td align="left">The lowest value of the gauge.</td>
</tr>
<tr class="even">
<td align="left">Gauge Max</td>
<td align="left">The highest value of the gauge.</td>
</tr>
<tr class="odd">
<td align="left">Stops</td>
<td align="left">The number of color ranges on the gauge.</td>
</tr>
<tr class="even">
<td align="left">Show Timestamp</td>
<td align="left">Show the timestamp of the current gauge measurement.</td>
</tr>
</tbody>
</table>

### Camera Widget

Cameras may be added to keep a continuous view on areas.

<table>
<col width="40%" />
<col width="59%" />
<thead>
<tr class="header">
<th align="left">Setting</th>
<th align="left">Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td align="left">Refresh (seconds)</td>
<td align="left">The duration between acquisitions of new data to display on the graph.</td>
</tr>
<tr class="even">
<td align="left">Max Age (seconds)</td>
<td align="left">The maximum allowed age of the image timestamp before a &quot;No Recent Image&quot; message is returned.</td>
</tr>
<tr class="odd">
<td align="left">Acquire Image (and save new file)</td>
<td align="left">Acquire a new images and save the previous image.</td>
</tr>
<tr class="even">
<td align="left">Acquire Image (and erase last file)</td>
<td align="left">Acquire a new image but erase the previous image.</td>
</tr>
<tr class="odd">
<td align="left">Display Live Video Stream</td>
<td align="left">Automatically start a video stream and display it.</td>
</tr>
<tr class="even">
<td align="left">Display Latest Timelapse Image</td>
<td align="left">Display the latest timelapse image that exists.</td>
</tr>
<tr class="odd">
<td align="left">Add Timestamp</td>
<td align="left">Append a timestamp to the image.</td>
</tr>
</tbody>
</table>

### Indicator Widget

Shows a green or red button depending if the measurement value is 0 or not 0.

<table>
<col width="40%" />
<col width="59%" />
<thead>
<tr class="header">
<th align="left">Setting</th>
<th align="left">Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td align="left">Refresh (seconds)</td>
<td align="left">The duration between acquisitions of new data to display on the graph.</td>
</tr>
<tr class="even">
<td align="left">Max Age (seconds)</td>
<td align="left">The maximum allowable age of the measurement. If the age is greater than this, the gauge will turn off, indicating there is an issue.</td>
</tr>
<tr class="odd">
<td align="left">Timestamp Font Size (em)</td>
<td align="left">The font size of the timestamp value in em.</td>
</tr>
<tr class="even">
<td align="left">Invert</td>
<td align="left">Invert/reverse the colors.</td>
</tr>
<tr class="odd">
<td align="left">Measurement</td>
<td align="left">The device to display information about.</td>
</tr>
</tbody>
</table>

### Measurement Widget

<table>
<col width="40%" />
<col width="59%" />
<thead>
<tr class="header">
<th align="left">Setting</th>
<th align="left">Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td align="left">Refresh (seconds)</td>
<td align="left">The duration between acquisitions of new data to display on the graph.</td>
</tr>
<tr class="even">
<td align="left">Max Age (seconds)</td>
<td align="left">The maximum allowable age of the measurement. If the age is greater than this, the gauge will turn off, indicating there is an issue.</td>
</tr>
<tr class="odd">
<td align="left">Value Font Size (em)</td>
<td align="left">The font size of the measurement value in em.</td>
</tr>
<tr class="even">
<td align="left">Timestamp Font Size (em)</td>
<td align="left">The font size of the timestamp value in em.</td>
</tr>
<tr class="odd">
<td align="left">Decimal Places</td>
<td align="left">The number of digits to display to the right of the decimal.</td>
</tr>
<tr class="even">
<td align="left">Measurement</td>
<td align="left">The device to display information about.</td>
</tr>
</tbody>
</table>

### Output Widget

<table>
<col width="40%" />
<col width="59%" />
<thead>
<tr class="header">
<th align="left">Setting</th>
<th align="left">Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td align="left">Refresh (seconds)</td>
<td align="left">The duration between acquisitions of new data to display on the graph.</td>
</tr>
<tr class="even">
<td align="left">Max Age (seconds)</td>
<td align="left">The maximum allowable age of the measurement. If the age is greater than this, the gauge will turn off, indicating there is an issue.</td>
</tr>
<tr class="odd">
<td align="left">Value Font Size (em)</td>
<td align="left">The font size of the output value in em.</td>
</tr>
<tr class="even">
<td align="left">Timestamp Font Size (em)</td>
<td align="left">The font size of the timestamp value in em.</td>
</tr>
<tr class="odd">
<td align="left">Decimal Places</td>
<td align="left">The number of digits to display to the right of the decimal.</td>
</tr>
<tr class="even">
<td align="left">Feature Output Controls</td>
<td align="left">Display buttons to turn On and Off the relay from the dashboard element.</td>
</tr>
<tr class="odd">
<td align="left">Output</td>
<td align="left">The output to display information about.</td>
</tr>
</tbody>
</table>

### PID Control Widget

<table>
<col width="40%" />
<col width="59%" />
<thead>
<tr class="header">
<th align="left">Setting</th>
<th align="left">Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td align="left">Refresh (seconds)</td>
<td align="left">The duration between acquisitions of new data to display on the graph.</td>
</tr>
<tr class="even">
<td align="left">Max Age (seconds)</td>
<td align="left">The maximum allowable age of the measurement. If the age is greater than this, the gauge will turn off, indicating there is an issue.</td>
</tr>
<tr class="odd">
<td align="left">Value Font Size (em)</td>
<td align="left">The font size of the measurement value in em.</td>
</tr>
<tr class="even">
<td align="left">Timestamp Font Size (em)</td>
<td align="left">The font size of the timestamp value in em.</td>
</tr>
<tr class="odd">
<td align="left">Decimal Places</td>
<td align="left">The number of digits to display to the right of the decimal.</td>
</tr>
<tr class="even">
<td align="left">Show PID Information</td>
<td align="left">Show extra PID information on the dashboard element.</td>
</tr>
<tr class="odd">
<td align="left">Show Set Setpoint</td>
<td align="left">Allow setting the PID setpoint on the dashboard element.</td>
</tr>
<tr class="even">
<td align="left">PID</td>
<td align="left">The PID to display information about.</td>
</tr>
</tbody>
</table>
