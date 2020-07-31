`Setup -> LCD`

Data may be output to a liquid crystal display (LCD) for easy viewing. Please see [LCD Displays](#lcd-displays) for specific information regarding compatibility.

There may be multiple displays created for each LCD. If there is only one display created for the LCD, it will refresh at the set period. If there is more than one display, it will cycle from one display to the next every set period.

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
<td align="left">Reset Flashing</td>
<td align="left">If the LCD is flashing to alert you because it was instructed to do so by a triggered Conditional Statement, use this button to stop the flashing.</td>
</tr>
<tr class="even">
<td align="left">Type</td>
<td align="left">Select either a 16x2 or 20x4 character LCD display.</td>
</tr>
<tr class="odd">
<td align="left">I2C Address</td>
<td align="left">Select the I2C to communicate with the LCD.</td>
</tr>
<tr class="even">
<td align="left">Period</td>
<td align="left">This is the period of time (in seconds) between redrawing the LCD with new data or switching to the next set of displays (if multiple displays are used).</td>
</tr>
<tr class="odd">
<td align="left">Add Display Set</td>
<td align="left">Add a set of display lines to the LCD.</td>
</tr>
<tr class="even">
<td align="left">Display Line #</td>
<td align="left">Select which measurement to display on each line of the LCD.</td>
</tr>
<tr class="odd">
<td align="left">Max Age (seconds)</td>
<td align="left">The maximum age the measurement is allowed to be. If no measurement was acquired in this time frame, the display will indicate &quot;NO DATA&quot;.</td>
</tr>
</tbody>
</table>