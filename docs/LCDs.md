Page\: `Setup -> LCD`

!!! warning
    LCD controllers have been deprecated since Mycodo version 8.9.0. All LCD controller functionality has been ported to [Functions](Functions.md). No new LCD controllers can be created in Mycodo 8.9.0 and beyond, but already-existing LCD controllers are permitted to operate until further notice. If you are using Mycodo version 8.9.0 or beyond, it is advised to create Functions for all your current LCD controllers, because at some point in the future LCD controllers will be completely removed. This manual page only serves as reference material for those still using LCD controllers.

Data may be output to a liquid crystal display (LCD) for easy viewing. Please see [LCD Displays](Device-Notes.md#lcd-displays) for specific information regarding compatibility.

There may be multiple displays created for each LCD. If there is only one display created for the LCD, it will refresh at the set period. If there is more than one display, it will cycle from one display to the next every set period.

<table>
<thead>
<tr class="header">
<th>Setting</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td>Reset Flashing</td>
<td>If the LCD is flashing to alert you because it was instructed to do so by a triggered Conditional Statement, use this button to stop the flashing.</td>
</tr>
<tr>
<td>Type</td>
<td>Select either a 16x2 or 20x4 character LCD display.</td>
</tr>
<tr>
<td>I2C Address</td>
<td>Select the I2C to communicate with the LCD.</td>
</tr>
<tr>
<td>Period</td>
<td>This is the period of time (in seconds) between redrawing the LCD with new data or switching to the next set of displays (if multiple displays are used).</td>
</tr>
<tr>
<td>Add Display Set</td>
<td>Add a set of display lines to the LCD.</td>
</tr>
<tr>
<td>Display Line #</td>
<td>Select which measurement to display on each line of the LCD.</td>
</tr>
<tr>
<td>Max Age (seconds)</td>
<td>The maximum age the measurement is allowed to be. If no measurement was acquired in this time frame, the display will indicate &quot;NO DATA&quot;.</td>
</tr>
</tbody>
</table>